import json
import ndjson
import sys


def extract_fields(entry):
    id = entry.get("id", "")
    title = entry.get("title", "")
    authors = entry.get("authors", {}).get("primary", {})
    if authors:
        authors = list(authors.keys())
    publication_dates = entry.get("publicationDates", [])
    subjects = [
        subject["heading"][0]
        for subject in entry.get("subjectsExtended", [])
        if "heading" in subject if subject["source"] == "yso/fin"
    ]

    return {
        "id": id,
        "title": title,
        "authors": authors,
        "publicationDates": publication_dates,
        "subjects": subjects,
    }


if __name__ == "__main__":
    input_data = sys.stdin.read()

    try:
        parsed_data = ndjson.loads(input_data)
    except ValueError:
        print("Invalid ndjson format")
        sys.exit(1)

    extracted_fields = [extract_fields(entry) for entry in parsed_data]
    for entry in extracted_fields:
        print(json.dumps(entry))
