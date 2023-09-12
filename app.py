import os
import sqlite3
import uuid

from elasticsearch import Elasticsearch
from flask import Flask, jsonify, redirect, render_template, request, session

app = Flask(__name__)
app.secret_key = "super secret key"
app.config[
    "SESSION_TYPE"
] = "filesystem"  # You can also use other session types like 'redis'

es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
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
            is_found INTEGER,
            labels_set TEXT,
            search_count INT,
            search_terms TEXT,
            search_begin_time_utc TEXT,
            search_end_time_utc TEXT,
            abandon_time_utc TEXT,
            uid TEXT
        )
    """
    )


@app.route("/")
def index():
    if "uid" not in session:
        session["uid"] = uuid.uuid4()
    print(f"User {session['uid']}")
    return render_template("index.html")


@app.route("/<labels_set>/search_page")
def search_page_fn(labels_set):
    session["search_count"] = 0
    return render_template("search-page.html")


@app.route("/<labels_set>/abandon", methods=["POST"])
def abandon_fn(labels_set):
    title = request.form.get("title")
    authors = request.form.get("authors")
    labels_set = labels_set
    search_count = session["search_count"]
    search_begin_time_utc = request.form.get("search_begin_time_utc")
    abandon_time_utc = request.form.get("abandonTime")
    uid = str(session["uid"])
    print(f"Book not found: {title} - {authors}")

    # Connect to the SQLite database
    with sqlite3.connect(sqlite3_db_path) as connection:
        cursor = connection.cursor()
        # Create the table if it doesn't exist
        create_table(cursor)

        # Insert the selected result into the database
        cursor.execute(
            """
            INSERT INTO selected_books (
                title,
                authors,
                is_found,
                labels_set,
                search_count,
                search_begin_time_utc,
                abandon_time_utc,
                uid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                title,
                authors,
                0,  # Not found
                labels_set,
                search_count,
                search_begin_time_utc,
                abandon_time_utc,
                uid,
            ),
        )

    # The used labels set needs to be retained
    return redirect(f"/{labels_set}/search_page")


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


@app.route("/<labels_set>/search", methods=["GET"])
def search_fn(labels_set):
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Missing 'q' parameter"}), 400

    search_terms = query.split(",")
    search_terms = [t.strip() for t in search_terms if t.strip()]
    search_target_field = f"subjects-{labels_set}-labels"
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
                "isbn": 9789512423514,  # TODO Replace with real isbn
            }
            results.append(result)
        session["search_count"] += 1
        print(f"Search count is {session['search_count']}")
        return jsonify({"results_count": hits_count, "results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/<labels_set>/select", methods=["POST"])
def select_fn(labels_set):
    title = request.form.get("title")
    authors = request.form.get("authors")
    year = request.form.get("year")
    isbn = request.form.get("isbn")
    labels_set = labels_set
    search_count = session["search_count"]
    search_terms = request.form.get("search_terms")
    search_begin_time_utc = request.form.get("search_begin_time_utc")
    search_end_time_utc = request.form.get("search_end_time_utc")
    uid = str(session["uid"])

    # Connect to the SQLite database
    with sqlite3.connect(sqlite3_db_path) as connection:
        cursor = connection.cursor()
        # Create the table if it doesn't exist
        create_table(cursor)

        # Insert the selected result into the database
        cursor.execute(
            """
            INSERT INTO selected_books (
                title,
                authors,
                year,
                isbn,
                is_found,
                labels_set,
                search_terms,
                search_count,
                search_begin_time_utc,
                search_end_time_utc,
                uid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                title,
                authors,
                year,
                isbn,
                1,  # is found
                labels_set,
                search_terms,
                search_count,
                search_begin_time_utc,
                search_end_time_utc,
                uid,
            ),
        )

    session["search_count"] = 0
    return jsonify({"message": "Result selected and saved successfully"})


@app.route("/<labels_set>/get_selected_books", methods=["GET"])
def get_selected_books_fn(labels_set):
    # Retrieve selected books for the current user and labels set
    user_selected_books = []

    with sqlite3.connect(sqlite3_db_path) as connection:
        cursor = connection.cursor()

        create_table(cursor)
        cursor.execute(
            """
            SELECT title, authors, is_found FROM selected_books
            WHERE uid = ? AND labels_set = ? ORDER BY search_begin_time_utc ASC
        """,
            (str(session["uid"]), labels_set),
        )

        rows = cursor.fetchall()
        for title, authors, is_found in rows:
            user_selected_books.append(
                {
                    "title": title,
                    "authors": authors,
                    "is_found": is_found,
                }
            )

    return jsonify({"selectedBooks": user_selected_books})


if __name__ == "__main__":
    app.run(debug=True)
