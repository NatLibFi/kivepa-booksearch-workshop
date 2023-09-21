import gzip
import json
from time import sleep

from annif_client import AnnifClient

BOOKS_FILE = "ks-bib.json.gz"  # File to read data from
ANNIF_SUBJECTS_FILE = "annif-subjects.json"  # File to save subjects to
ANNIF_API_BASE = "https://dev.annif.org/v1/"
PROJECT_ID = "kauno-ensemble-fi"


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


def annif_suggest(text):
    results = annif.suggest(project_id=PROJECT_ID, text=text)
    return [res["uri"] for res in results]


annif = AnnifClient(api_base=ANNIF_API_BASE)

# Read books from file
with gzip.open(BOOKS_FILE, "rt") as books_file:
    books = json.loads(books_file.read())["results"]["bindings"]
print(f"Read {len(books)} books from file")


books_annif_subjects = dict()
errored = 0
cnt = 0
for book_json in books:
    try:
        book = parse_book_json(book_json)
    except KeyError as err:
        print(f"Key not found: {err}")
        errored += 1
        continue

    # Skip duplicates
    if book["work-uri"] in books_annif_subjects:
        continue
    try:
        book_annif_subjects = annif_suggest(book["desc"])
    except Exception as err:
        print(f"annif-suggest error: {err}")
        continue

    books_annif_subjects[book["work-uri"]] = book_annif_subjects

    cnt += 1
    if cnt % 100 == 0:
        print(f"Suggestions for {cnt} books...")
        sleep(1)
    # if cnt >= 100:  # TMP, for getting small dev set
    #     break

print(f"Saving annif subjects for {len(books_annif_subjects)} books")
# Save subjects to a file
with open(ANNIF_SUBJECTS_FILE, "w") as outfile:
    json.dump(books_annif_subjects, outfile)

print(f"Number of books skipped: {errored}")
