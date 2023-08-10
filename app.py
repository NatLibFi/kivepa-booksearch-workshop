import sqlite3
import random
from flask import Flask, request, render_template, jsonify, session
from flask_session import Session
from elasticsearch import Elasticsearch

app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'  # You can also use other session types like 'redis'

es = Elasticsearch("http://localhost:9200")


@app.route("/")
def index():
    session['source'] = random.choice(["a", "b"])
    return render_template("index.html")


@app.route("/search", methods=["GET"])
def search_books():
    print(session["source"])
    query = request.args.get("q", "")  # Get the 'q' parameter from the query string
    if not query:
        return jsonify({"error": "Missing 'q' parameter"}), 400


    body = {"query": {"match": {f"subjects-{session['source']}": query}}}
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
                "year": source.get("publicationDates", "N/A"),
                "score": hit["_score"],
            }
            results.append(result)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/select', methods=['POST'])
def select_result():
    selected_title = request.form.get('title')
    selected_authors = request.form.get('authors')
    selected_year = request.form.get('year')
    source = session["source"]

    # Connect to the SQLite database
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    # Insert the selected result into the database
    cursor.execute('''
        INSERT INTO selected_books (title, authors, year, source)
        VALUES (?, ?, ?, ?)
    ''', (selected_title, selected_authors, selected_year, source))

    # Commit the changes and close the connection
    connection.commit()
    connection.close()

    session['source'] = random.choice(["a", "b"])

    return jsonify({"message": "Result selected and saved successfully"})


if __name__ == "__main__":
    app.run(debug=True)
