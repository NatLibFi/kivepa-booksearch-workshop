from elasticsearch import Elasticsearch, helpers
import sys
import json
import requests
from time import sleep

from annif_client import AnnifClient


# Connect to Elasticsearch
es = Elasticsearch(["http://localhost:9200"])
# Define the index name
index_name = "books"


API_BASE = 'https://ai.dev.finto.fi/v1/'
PROJECT_ID = 'kauno-ensemble-fi'
annif = AnnifClient(api_base=API_BASE)


def parse_book_json(book):
    document = {}
    document["work-uri"] = book["work"]["value"]
    document["subjects-a-uris"] = book["themes"]["value"].split()
    document["title"] = book["title"]["value"]
    document["authors"] = book["authorNames"]["value"]
    document["desc"] = book["desc"]["value"]
    document["isbn"] = "1234"  # TODO Needs to adjust the SPARQL
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
    return labels


def annif_suggest(text):
    results = annif.suggest(project_id=PROJECT_ID, text=text)
    return [res['uri'] for res in results]


data = json.loads(sys.stdin.read())
books = data["results"]["bindings"]

actions = []
loaded_books = set()
errored = 0
cnt = 0
for book in books:
    cnt += 1
    try:
        document = parse_book_json(book)  # to be imported to Elasticsearch
    except KeyError as err:
        print(f"Key not found: {err}")
        errored += 1

    # Skip importing duplicates
    if document["work-uri"] in loaded_books:
        continue
    loaded_books.add(document["work-uri"])

    document["subjects-a-labels"] = resolve_uris_to_labels(document["subjects-a-uris"])
    document["subjects-b-uris"] = annif_suggest(document["desc"])
    document["subjects-b-labels"] = resolve_uris_to_labels(document["subjects-b-uris"])

    action = {"_index": index_name, "_source": document}
    actions.append(action)

    sleep(1)
    if cnt >= 200:  # TMP, for getting small dev set
        break

    if len(actions) >= 100:  # Adjust batch size as needed
        print("Importing 100-documents batch...")
        helpers.bulk(es, actions)
        actions = []
        print("Done")

if actions:
    helpers.bulk(es, actions)

print(f"Number of books skipped: {errored}")
