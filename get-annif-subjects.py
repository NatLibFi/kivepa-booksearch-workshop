import gzip
import json
from time import sleep

from annif_client import AnnifClient

BOOKS_FILE = "ks-bib-for-kivepa-prototype.json.gz"
ANNIF_SUBJECTS_FILE = "annif-subjects.json"  # File to save subjects to
ANNIF_API_BASE = "https://dev.annif.org/v1/"
PROJECT_ID = "kauno-ensemble-fi"
# limit and threshold values for best f1 score given by optimize run
LIMIT = 18
THRESHOLD = 0.16


def parse_book_json(book):
    document = {}
    document["work-uri"] = book["work"]["value"]
    document["title"] = book["title"]["value"]
    document["authors"] = book["authorNames"]["value"]
    document["desc"] = book["desc"]["value"]
    document["year"] = book["minPublished"]["value"]
    return document


def annif_suggest(text):
    results = annif.suggest(
        project_id=PROJECT_ID, text=text, limit=LIMIT, threshold=THRESHOLD
    )
    return [res["uri"] for res in results]


annif = AnnifClient(api_base=ANNIF_API_BASE)

# Read books from file
with gzip.open(BOOKS_FILE, "rt") as books_file:
    books = json.loads(books_file.read())["results"]["bindings"]
print(f"Read {len(books)} books from file")

# Order by year, descending
# books = sorted(
#     books, key=lambda x: x.get("pubLabel", {}).get("value", "0001"), reverse=True
# )


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

    if book["year"] < "2022":
        continue

    # Skip duplicates
    if book["work-uri"] in books_annif_subjects:
        continue
    try:
        text = book["title"] + " " + book["desc"]
        book_annif_subjects = annif_suggest(text)
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
