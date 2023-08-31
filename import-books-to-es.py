from elasticsearch import Elasticsearch, helpers
import gzip
import sys
import json
import requests
from time import sleep


# Connect to Elasticsearch
if len(sys.argv) > 1:
    es_url = sys.argv[1]
else:
    es_url = "http://localhost:9200"
es = Elasticsearch(es_url)

# Define the index name
index_name = "books"

FINTO_API_QUERY_BASE = "https://api.finto.fi/rest/v1/label"


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


def resolve_uris_to_labels(uris):
    labels = []
    for uri in uris:
        params = {"uri": uri, "lang": "fi"}
        resp = requests.get(FINTO_API_QUERY_BASE, params=params)
        if resp.ok:
            try:
                label = resp.json()["prefLabel"]
            except json.decoder.JSONDecodeError as err:
                print(err)
                print(resp)
            labels.append(label)
    return labels


# Read books from file
with gzip.open('ks-bib.json.gz', 'rt') as books_file:
    books = json.loads(books_file.read())["results"]["bindings"]
print(f"Read {len(books)} books from file")


with open('annif-subjects.json', 'rt') as as_file:
    books_annif_subjects = json.loads(as_file.read())
print(f"Read annif subjects for {len(books_annif_subjects)} books")


actions = []
loaded_books = set()
errored = 0
cnt = 0
for book_json in books:
    cnt += 1
    try:
        book = parse_book_json(book_json)  # to be imported to Elasticsearch
    except KeyError as err:
        print(f"Key not found: {err}")
        errored += 1
        continue

    # Skip importing duplicates
    if book["work-uri"] in loaded_books:
        continue
    loaded_books.add(book["work-uri"])

    book["subjects-a-labels"] = resolve_uris_to_labels(book["subjects-a-uris"])
    book["subjects-b-uris"] = books_annif_subjects[book["work-uri"]]
    book["subjects-b-labels"] = resolve_uris_to_labels(book["subjects-b-uris"])

    action = {"_index": index_name, "_source": book}
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
