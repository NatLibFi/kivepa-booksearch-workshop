import csv
import gzip
import json
import sys
from time import sleep

import requests
from elasticsearch import Elasticsearch, helpers

# Files to read data from
BOOKS_FILE = "ks-bib-for-kivepa-prototype.json.gz"
ANNIF_SUBJECTS_FILE = (
    "annif-subjects.json"  # work-uris as keys, subjects-uris as values
)
KOKO_TO_KAUNO_FILE = "koko_to_kauno_yso.csv"

# The Elasticsearch index name
index_name = "books"

# Endpoint for querying labels of uris
FINTO_API_QUERY_BASE = "https://api.finto.fi/rest/v1/label"


# Connect to Elasticsearch
if len(sys.argv) > 1:
    es_url = sys.argv[1]
else:
    es_url = "http://localhost:9200"
es = Elasticsearch(es_url)
print(f"Connected to Elasticsearch at: {es_url}")


def parse_book_json(book):
    document = {}
    document["work-uri"] = book["work"]["value"]
    themes = book.get("themes", {}).get("value", "").split()
    agents = book.get("agents", {}).get("value", "").split()
    places = book.get("places", {}).get("value", "").split()
    times = book.get("times", {}).get("value", "").split()
    # TODO Add genres too?
    # Subjects fields are not present in json file
    document["subjects-a-uris"] = themes + agents + places + times
    document["title"] = book["title"]["value"]
    document["authors"] = book["authorNames"]["value"]
    document["isbn"] = book["isbn"]["value"]
    document["year"] = book["minPublished"]["value"]
    document["desc"] = book["desc"]["value"]
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
with gzip.open(BOOKS_FILE, "rt") as books_file:
    books = json.loads(books_file.read())["results"]["bindings"]
print(f"Read {len(books)} books from file")

with open(ANNIF_SUBJECTS_FILE, "rt") as subjs_file:
    books_annif_subjects = json.loads(subjs_file.read())
print(f"Read annif subjects for {len(books_annif_subjects)} books")

subjects_map = {}
with open(KOKO_TO_KAUNO_FILE, "r") as mapping_file:
    csv_reader = csv.reader(mapping_file)
    for row in csv_reader:
        subjects_map[row[0]] = row[1]


# Define the index mapping
index_mapping = {
    "mappings": {
        "properties": {
            "work-uri": {"type": "keyword"},
            "authors": {"type": "keyword"},
            "title": {"type": "keyword"},
            "isbn": {"type": "keyword"},
            "year": {"type": "integer"},
            "subjects-a-uris": {"type": "keyword"},
            "subjects-a-labels": {"type": "keyword"},
            "subjects-b-uris": {"type": "keyword"},
            "subjects-b-labels": {"type": "keyword"},
            "desc": {"type": "text"},
        }
    }
}

# Create the index with the specified mapping
es.indices.create(index=index_name, body=index_mapping)  # , ignore=400)


actions = []
loaded_books = set()
errored = 0
skipped = 0
for book_json in books:
    # if len(loaded_books) >= 10:  # TMP, for getting small dev set
    #     break

    try:
        book = parse_book_json(book_json)  # to be imported to Elasticsearch
    except KeyError as err:
        print(
            f"Failed parsing book - Key not found: {err}\n{book_json}\n",
        )
        errored += 1
        continue

    if book["year"] < "2022":
        continue

    # Skip importing duplicates
    if book["work-uri"] in loaded_books:
        skipped += 1
        continue

    # Map KOKO uris to KAUNO uris
    try:
        book["subjects-a-uris"] = [
            subjects_map[kauno_uri] for kauno_uri in book["subjects-a-uris"]
        ]
    except KeyError as err:
        print(
            f"Failed mapping subjects - Key not found: {err}\nBook title: {book['title']}",
        )
        errored += 1
        continue

    try:
        book["subjects-b-uris"] = books_annif_subjects[book["work-uri"]]
    except KeyError as err:
        print(
            f"Failed getting Annif subjects - Key not found: {err}\nBook title: {book['title']}",
        )
        errored += 1
        continue
    try:
        book["subjects-a-labels"] = resolve_uris_to_labels(book["subjects-a-uris"])
    except Exception as err:
        print(
            f"URI resolving failed for set A\nBook title: {book['title']}\n{err}",
        )
        continue
    try:
        book["subjects-b-labels"] = resolve_uris_to_labels(book["subjects-b-uris"])
    except Exception as err:
        print(
            f"URI resolving failed for set B\nBook title: {book['title']}\n{err}",
        )
        continue

    action = {"_index": index_name, "_source": book}
    actions.append(action)
    loaded_books.add(book["work-uri"])

    if len(actions) >= 100:  # Adjust batch size as needed
        print("Importing 100-documents batch...")
        helpers.bulk(es, actions)
        actions = []
        print(f"Number of books imported: {len(loaded_books)}")
        sleep(1)

if actions:
    helpers.bulk(es, actions)

print("All done.")
print(f"Number of books imported: {len(loaded_books)}")
print(f"Number of books errored: {errored}")
print(f"Number of duplicate books skipped: {skipped}")
