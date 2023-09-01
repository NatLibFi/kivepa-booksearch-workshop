import os
import sqlite3
import random
import uuid
from datetime import datetime, timezone
from flask import Flask, request, render_template, jsonify, session
from elasticsearch import Elasticsearch

app = Flask(__name__)
app.secret_key = "super secret key"
app.config[
    "SESSION_TYPE"
] = "filesystem"  # You can also use other session types like 'redis'

es_url = os.getenv("elasticsearch-url", "http://localhost:9200")
es = Elasticsearch(es_url)


def create_table(cursor):
    # Create a table if it doesn't exist
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS selected_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            authors TEXT,
            year INTEGER,
            labels_set TEXT,
            isbn INTEGER,
            searchTerms TEXT,
            selectionTimeUtc TEXT,
            uid TEXT
        )
    """
    )


@app.route("/")
def index():
    if "uid" not in session:
        session["uid"] = uuid.uuid4()
    session["labels_set"] = random.choice(["a", "b"])
    print(f"User {session['uid']}")
    print(f"Using labels set {session['labels_set']}")
    return render_template("index.html")


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

    body = {"query": {"match": {f"subjects-{session['labels_set']}-labels": query}}}
    # body = {"query": {"fuzzy": {"subjects": {"value": query}}}}

    try:
        response = es.search(index="books", body=body)
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
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/select", methods=["POST"])
def select_result():
    selected_title = request.form.get("title")
    selected_authors = request.form.get("authors")
    selected_year = request.form.get("year")
    selected_isbn = request.form.get("isbn")
    search_terms = request.form.get("searchTerms")
    used_labels_set = session["labels_set"]
    uid = str(session["uid"])
    current_time_utc = str(datetime.now(timezone.utc))

    # Connect to the SQLite database
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    create_table(cursor)

    # Insert the selected result into the database
    cursor.execute(
        """
        INSERT INTO selected_books (title, authors, year, labels_set, isbn,
        searchTerms, selectionTimeUtc, uid)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            selected_title,
            selected_authors,
            selected_year,
            used_labels_set,
            selected_isbn,
            search_terms,
            current_time_utc,
            uid,
        ),
    )

    # Commit the changes and close the connection
    connection.commit()
    connection.close()

    session["labels-set"] = random.choice(["a", "b"])
    print(f"User {session['uid']}")
    print(f"Using labels set {session['labels_set']}")
    return jsonify({"message": "Result selected and saved successfully"})


@app.route("/get_selected_books", methods=["GET"])
def get_selected_books():
    # Retrieve selected books for the current user (using session or any other user identification method)
    # You might need to modify this logic based on how you identify users
    user_selected_books = []

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    create_table(cursor)
    cursor.execute(
        """
        SELECT title, authors, labels_set FROM selected_books
        WHERE uid = ? ORDER BY selectionTimeUtc ASC
    """,
        (str(session["uid"]),),
    )

    rows = cursor.fetchall()
    for row in rows:
        title, authors, labels_set = row
        user_selected_books.append({"title": title, "authors": authors, "labels_set": labels_set.upper()})

    connection.close()

    return jsonify({"selectedBooks": user_selected_books})


if __name__ == "__main__":
    app.run(debug=True)
