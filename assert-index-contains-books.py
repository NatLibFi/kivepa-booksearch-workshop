import sys
from elasticsearch import Elasticsearch


# Connect to Elasticsearch
if len(sys.argv) > 1:
    es_url = sys.argv[1]
else:
    es_url = "http://localhost:9200"
es = Elasticsearch(es_url)

book_titles = [
    "Harjoitukset",
    "Alfauros",
    "Neuvostoihmisen loppu",
    "Salajuoni Amerikkaa vastaan",
    "Isän kanssa kahden",
    "Kuolleet sielut",
    "Kvanttivaras",
    "Taivas",
    "Tokio ei välitä meistä enää",
    # "Tätä ei ole",
]
size = 100
for bt in book_titles:
    resp = es.search(
        index="books",
        query={"match": {"title": {"query": bt, "operator": "and"}}},
        size=size,
    )
    if resp["hits"]["total"]["value"] >= size:
        raise AssertionError(
            f'Number of matches ({resp["hits"]["total"]["value"]}) exceeds search size.'
        )
    for hit in resp["hits"]["hits"]:
        book = hit["_source"]
        if bt == book["title"]:
            # print(bt, " - ", book["title"])
            break
    else:
        raise AssertionError(f"Book not in index: {bt}")
