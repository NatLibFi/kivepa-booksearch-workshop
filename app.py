from flask import Flask, request, render_template, jsonify
from elasticsearch import Elasticsearch

app = Flask(__name__)
es = Elasticsearch("http://localhost:9200")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["GET"])
def search_books():
    query = request.args.get("q", "")  # Get the 'q' parameter from the query string
    if not query:
        return jsonify({"error": "Missing 'q' parameter"}), 400

    body = {"query": {"match": {"subjects": query}}}
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

    # Process the selected result as needed
    # You can save it to a database, session, or perform any other action
    print(f"Selected {selected_title} by {selected_authors}")
    return jsonify({"message": "Result selected successfully"})

if __name__ == "__main__":
    app.run(debug=True)
