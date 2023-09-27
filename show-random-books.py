import random
import sys

from elasticsearch import Elasticsearch

LIMIT = 10
INDEX = "books"

# Connect to Elasticsearch
if len(sys.argv) > 1:
    es_url = sys.argv[1]
else:
    es_url = "http://localhost:9200"
es = Elasticsearch(es_url)
print(f"Connected to Elasticsearch at: {es_url}")


scroll_time = "1m"  # Adjust this according to your needs
query = {"query": {"match_all": {}}}  # You can customize the query if needed

# Initialize the scroll
response = es.search(index=INDEX, scroll=scroll_time, body=query)
scroll_id = response["_scroll_id"]

books = []

documents = []
# Iterate through the results using the scroll API
while True:
    # Get the documents from the current scroll
    scroll_documents = response["hits"]["hits"]

    # Extract field values from each document
    for doc in scroll_documents:
        documents.append(
            (doc["_source"]["title"], doc["_source"]["authors"], doc["_source"]["desc"])
        )

    # Perform the next scroll
    response = es.scroll(scroll_id=scroll_id, scroll=scroll_time)

    # Stop when there are no more documents
    if not response["hits"]["hits"]:
        break

random.shuffle(documents)

for cnt, doc in enumerate(documents[:LIMIT]):
    print("Book number: ", cnt)
    print(doc[0], " | ", doc[1])
    print(doc[2])
    print("-" * 100)
