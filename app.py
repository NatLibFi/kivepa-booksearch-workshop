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


def create_books_table(cursor):
    # Create a table if it doesn't exist
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS searched_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            authors TEXT,
            is_found_a INTEGER,
            is_found_b INTEGER,
            search_count_a INT,
            search_count_b INT,
            search_terms_a TEXT,
            search_terms_b TEXT,
            search_begin_time_utc TEXT,
            found_time_utc_a TEXT,
            found_time_utc_b TEXT,
            search_end_time_utc TEXT,
            uid TEXT
        )
    """
    )


def create_users_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_number INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT,
            UNIQUE(uid)
        )
    """
    )


def register_user(uid):
    with sqlite3.connect(sqlite3_db_path) as connection:
        cursor = connection.cursor()
        # Create the table if it doesn't exist
        create_users_table(cursor)

        cursor.execute(
            """
            INSERT OR IGNORE INTO users (uid) VALUES (?)
        """,
            (str(uid),),
        )


@app.route("/")
def index():
    if "uid" not in session:
        session["uid"] = uuid.uuid4()
        register_user(session["uid"])
        print(f"Registered user with uid {session['uid']}")
    return render_template("index.html")


@app.route("/get_user_number")
def get_user_number():
    uid = str(session["uid"])
    # Connect to the SQLite database and fetch the user_number
    with sqlite3.connect(sqlite3_db_path) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT user_number FROM users WHERE uid = ? LIMIT 1", (uid,))
        user_number = cursor.fetchone()[0]
    return jsonify({"user_number": user_number})


@app.route("/proceed", methods=["POST"])
def proceed_fn():
    title = request.form.get("title")
    authors = request.form.get("authors")
    is_found_a = request.form.get("isBookFoundA")
    is_found_b = request.form.get("isBookFoundB")
    search_count_a = request.form.get("searchCountA")
    search_count_b = request.form.get("searchCountB")
    search_terms_a = request.form.get("searchTermsA")  # For which book is found
    search_terms_b = request.form.get("searchTermsB")
    search_begin_time_utc = request.form.get("searchBeginTimeUtc")
    search_end_time_utc = request.form.get("searchEndTimeUtc")
    found_time_utc_a = request.form.get("foundTimeA")
    found_time_utc_b = request.form.get("foundTimeB")
    uid = str(session["uid"])

    # Connect to the SQLite database
    with sqlite3.connect(sqlite3_db_path) as connection:
        cursor = connection.cursor()
        # Create the table if it doesn't exist
        create_books_table(cursor)

        # Insert the selected result into the database
        cursor.execute(
            """
            INSERT INTO searched_books (
                title,
                authors,
                is_found_a,
                is_found_b,
                search_count_a,
                search_count_b,
                search_terms_a,
                search_terms_b,
                search_begin_time_utc,
                found_time_utc_a,
                found_time_utc_b,
                search_end_time_utc,
                uid
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                title,
                authors,
                is_found_a,
                is_found_b,
                search_count_a,
                search_count_b,
                search_terms_a,
                search_terms_b,
                search_begin_time_utc,
                found_time_utc_a,
                found_time_utc_b,
                search_end_time_utc,
                uid,
            ),
        )

    # The used labels set needs to be retained
    return redirect("/")


@app.route("/autocomplete", methods=["GET"])
def autocomplete():
    query = request.args.get("q", "")

    if not query:
        return jsonify([])

    index = "autocomplete"
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


@app.route("/search/<labels_set>", methods=["GET"])
def search_fn(labels_set):
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Missing 'q' parameter"}), 400

    search_terms = query.split(",")
    search_terms = [t.strip() for t in search_terms if t.strip()]
    search_target_field = f"subjects-{labels_set}-labels"
    body = {
        "query": {
            "bool": {
                "should": [
                    {"term": {search_target_field: {"value": term}}}
                    for term in search_terms
                ],
                "minimum_should_match": 1,
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
                "isbn": source["isbn"],
                "labels": source[f"subjects-{labels_set}-labels"],
                "score": hit["_score"],
            }
            results.append(result)
        return jsonify({"results_count": hits_count, "results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/searched_books", methods=["GET"])
def get_searched_books_fn():
    # Retrieve selected books for the current user and labels set
    user_searched_books = []

    with sqlite3.connect(sqlite3_db_path) as connection:
        cursor = connection.cursor()

        create_books_table(cursor)
        cursor.execute(
            """
            SELECT title, authors, is_found_a, is_found_b FROM searched_books
            WHERE uid = ? ORDER BY id ASC
        """,
            (str(session["uid"]),),
        )

        rows = cursor.fetchall()
        for title, authors, is_found_a, is_found_b in rows:
            user_searched_books.append(
                {
                    "title": title,
                    "authors": authors,
                    "is_found_a": is_found_a == "true",
                    "is_found_b": is_found_b == "true",
                }
            )

    return jsonify({"searchedBooks": user_searched_books})


if __name__ == "__main__":
    app.run(debug=True)
