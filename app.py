import sqlite3
import random
from datetime import datetime, timezone
from flask import Flask, request, render_template, jsonify, session
from elasticsearch import Elasticsearch

app = Flask(__name__)
app.secret_key = "super secret key"
app.config[
    "SESSION_TYPE"
] = "filesystem"  # You can also use other session types like 'redis'

es = Elasticsearch("http://localhost:9200")


@app.route("/")
def index():
    session["source"] = random.choice(["a", "b"])
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
    print(session["source"])
    query = request.args.get("q", "")  # Get the 'q' parameter from the query string
    if not query:
        return jsonify({"error": "Missing 'q' parameter"}), 400

    body = {"query": {"match": {f"subjects-{session['source']}-labels": query}}}
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
    source = session["source"]
    current_time_utc = str(datetime.now(timezone.utc))

    # Connect to the SQLite database
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # Insert the selected result into the database
    cursor.execute(
        """
        INSERT INTO selected_books (title, authors, year, source, isbn,
        searchTerms, selectionTimeUtc)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            selected_title,
            selected_authors,
            selected_year,
            source,
            selected_isbn,
            search_terms,
            current_time_utc,
        ),
    )

    # Commit the changes and close the connection
    connection.commit()
    connection.close()

    session["source"] = random.choice(["a", "b"])

    return jsonify({"message": "Result selected and saved successfully"})


if __name__ == "__main__":
    app.run(debug=True)
