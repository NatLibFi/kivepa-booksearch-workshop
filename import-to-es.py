from elasticsearch import Elasticsearch, helpers
import sys
import json

# Connect to Elasticsearch
es = Elasticsearch(["http://localhost:9200"])

# Define the index name
index_name = "books"


# Function to index NDJSON data from stdin
def index_ndjson_from_stdin(index_name):
    actions = []
    for line in sys.stdin:
        document = json.loads(line)
        action = {"_index": index_name, "_source": document}
        actions.append(action)

        if len(actions) >= 1000:  # Adjust batch size as needed
            helpers.bulk(es, actions)
            actions = []

    if actions:
        helpers.bulk(es, actions)


# Call the function to index NDJSON data from stdin
index_ndjson_from_stdin(index_name)
