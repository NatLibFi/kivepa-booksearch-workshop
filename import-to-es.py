from elasticsearch import Elasticsearch, helpers
import sys
import json
import requests
from time import sleep


# Connect to Elasticsearch
es = Elasticsearch(["http://localhost:9200"])
# Define the index name
index_name = "books"


def parse_book_json(book):
    document = {}
    document["work-uri"] = book["work"]["value"]
    document["subjects-a-uris"] = book["themes"]["value"].split()
    document["title"] = book["title"]["value"]
    document["authors"] = book["authorNames"]["value"]
    # document["desc"] =
    # document["inst"] = book["inst"]["value"]
    document["year"] = book["pubLabel"]["value"]
    return document


finto_api_label_query_base = f"https://api.finto.fi/rest/v1/label"


def resolve_uris_to_labels(uris):
    labels = []
    for uri in uris:
        params = {"uri": uri, "lang": "fi"}
        resp = requests.get(finto_api_label_query_base, params=params)
        if resp.ok:
            try:
                label = resp.json()["prefLabel"]
            except json.decoder.JSONDecodeError as err:
                print(err)
                print(resp)
            labels.append(label)
        sleep(0.1)
    return labels


data = json.loads(sys.stdin.read())
books = data["results"]["bindings"]

actions = []
skipped = 0
cnt = 0
for book in books:
    cnt += 1
    try:
        document = parse_book_json(book)  # to be imported to Elasticsearch
    except KeyError as err:
        print(err)
        skipped += 1

    document["subjects-a-labels"] = resolve_uris_to_labels(document["subjects-a-uris"])

    action = {"_index": index_name, "_source": document}
    actions.append(action)

    if cnt >= 100:  # TMP, for getting small dev set
        break

    if len(actions) >= 1000:  # Adjust batch size as needed
        print("Importing 1k-documents batch")
        helpers.bulk(es, actions)
        actions = []

if actions:
    helpers.bulk(es, actions)

print(f"Number of books skipped: {skipped}")
