import os
import sqlite3
import random
import uuid
from datetime import datetime, timezone
from flask import Flask, request, render_template, jsonify, session, redirect
from elasticsearch import Elasticsearch

app = Flask(__name__)
app.secret_key = "super secret key"
app.config[
    "SESSION_TYPE"
] = "filesystem"  # You can also use other session types like 'redis'

es_url = os.getenv("elasticsearch_url", "http://localhost:9200")
es = Elasticsearch(es_url)
print(f"Connected to Elasticsearch at: {es_url}")

sqlite3_db_path = "sqlite3-data/database.db"


def create_table(cursor):
    # Create a table if it doesn't exist
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS selected_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            authors TEXT,
            year INTEGER,
            isbn INTEGER,
            labels_set TEXT,
            search_terms TEXT,
            search_count INT,
            selection_time_utc TEXT,
            uid TEXT
        )
    """
    )


@app.route("/")
def index():
    if "uid" not in session:
        session["uid"] = uuid.uuid4()
    session["labels_set"] = random.choice(["a", "b"])
    session["search_count"] = 0
    print(f"User {session['uid']}")
    print(f"Using labels set {session['labels_set']}")
    return render_template("index.html")


@app.route("/abandon", methods=["POST"])
def abandon_book():
    session["labels_set"] = random.choice(["a", "b"])
    print(f"Using labels set {session['labels_set']}")
    return redirect("/")


@app.route("/autocomplete", methods=["GET"])
def autocomplete():
    query = request.args.get("q", "")

    if not query:
        return jsonify([])

    index = "labels"
    field = "label_suggest"

    body = {
        "suggest": {
            "autocomplete": {
                "prefix": query,
                "completion": {
                    "field": field,
                    "size": 50,  # TODO How many suggestions to show?
                },
            }
        }
    }

    response = es.search(index=index, body=body)
    suggestions = response["suggest"]["autocomplete"][0]["options"]
    suggestion_values = [sugg["text"] for sugg in suggestions]

    return jsonify(suggestion_values)


@app.route("/search", methods=["GET"])
def search_books():
    query = request.args.get("q", "")  # Get the 'q' parameter from the query string
    if not query:
        return jsonify({"error": "Missing 'q' parameter"}), 400

    search_terms = query.split(",")
    search_terms = [t.strip() for t in search_terms if t.strip()]
    search_target_field = f"subjects-{session['labels_set']}-labels"
    body = {
        "query": {
            "terms_set": {
                search_target_field: {
                    "terms": search_terms,
                    "minimum_should_match_script": {"source": "params.num_terms"},
                }
            }
        }
    }

    try:
        response = es.search(index="books", body=body, size=10000)
        hits_count = response["hits"]["total"]["value"]
        hits = response["hits"]["hits"]
        results = []
        for hit in hits:
            source = hit["_source"]
            result = {
                "title": source["title"],
                "authors": source.get("authors", "N/A"),
                "year": source.get("year", "N/A"),
                "score": hit["_score"],
                "isbn": 9789512423514,  # TODO Replace with isbn from Elasticsearch
            }
            results.append(result)
        session["search_count"] += 1
        print(f"Search count is {session['search_count']}")
        return jsonify({"results_count": hits_count, "results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/select", methods=["POST"])
def select_result():
    selected_title = request.form.get("title")
    selected_authors = request.form.get("authors")
    selected_year = request.form.get("year")
    selected_isbn = request.form.get("isbn")
    used_labels_set = session["labels_set"]
    search_terms = request.form.get("search_terms")
    search_count = session["search_count"]
    current_time_utc = str(datetime.now(timezone.utc))
    uid = str(session["uid"])

    # Connect to the SQLite database
    connection = sqlite3.connect(sqlite3_db_path)
    cursor = connection.cursor()

    create_table(cursor)

    # Insert the selected result into the database
    cursor.execute(
        """
        INSERT INTO selected_books (title, authors, year, isbn, labels_set,
        search_terms, search_count, selection_time_utc, uid)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            selected_title,
            selected_authors,
            selected_year,
            selected_isbn,
            used_labels_set,
            search_terms,
            search_count,
            current_time_utc,
            uid,
        ),
    )

    # Commit the changes and close the connection
    connection.commit()
    connection.close()

    session["labels-set"] = random.choice(["a", "b"])
    session["search_count"] = 0

    print(f"User {session['uid']}")
    print(f"Using labels set {session['labels_set']}")
    return jsonify({"message": "Result selected and saved successfully"})


@app.route("/get_selected_books", methods=["GET"])
def get_selected_books():
    # Retrieve selected books for the current user (using session or any other user identification method)
    # You might need to modify this logic based on how you identify users
    user_selected_books = []

    connection = sqlite3.connect(sqlite3_db_path)
    cursor = connection.cursor()

    create_table(cursor)
    cursor.execute(
        """
        SELECT title, authors, labels_set, search_count FROM selected_books
        WHERE uid = ? ORDER BY selection_time_utc ASC
    """,
        (str(session["uid"]),),
    )

    rows = cursor.fetchall()
    for title, authors, labels_set, search_count in rows:
        user_selected_books.append(
            {
                "title": title,
                "authors": authors,
                "labels_set": labels_set.upper(),
                "search_count": search_count,
            }
        )

    connection.close()

    return jsonify({"selectedBooks": user_selected_books})


if __name__ == "__main__":
    app.run(debug=True)
