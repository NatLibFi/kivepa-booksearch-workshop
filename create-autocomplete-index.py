from elasticsearch import Elasticsearch, helpers

# Get all unique labels from two fields of an existing index
# and create a new index where they are used for autocompletion

es = Elasticsearch("http://localhost:9200")


# First get the labels

source_index_name = "books"
field_name_a = "subjects-a-labels"
field_name_b = "subjects-b-labels"

scroll_time = "1m"  # Adjust this according to your needs
query = {"query": {"match_all": {}}}  # You can customize the query if needed

# Initialize the scroll
response = es.search(index=source_index_name, scroll=scroll_time, body=query)
scroll_id = response["_scroll_id"]

# Set to store all field values
labels = set()

# Iterate through the results using the scroll API
while True:
    # Get the documents from the current scroll
    documents = response["hits"]["hits"]

    # Extract field values from each document
    for doc in documents:
        if field_name_a in doc["_source"]:
            labels.update(doc["_source"][field_name_a])
        if field_name_b in doc["_source"]:
            labels.update(doc["_source"][field_name_b])

    # Perform the next scroll
    response = es.scroll(scroll_id=scroll_id, scroll=scroll_time)

    # Stop when there are no more documents
    if not response["hits"]["hits"]:
        break

# Clear the scroll
es.clear_scroll(scroll_id=scroll_id)

print(f"Number of labels: {len(labels)}")


# Then create the new index

labels_index_name = "labels"
labels_field_name = "label_suggest"

labels_index_mapping = {
    "mappings": {"properties": {labels_field_name: {"type": "completion"}}}
}

es.indices.create(index=labels_index_name, body=labels_index_mapping)

# Populate the new index
actions = [
    {"_index": labels_index_name, "_source": {labels_field_name: label}}
    for label in labels
]
helpers.bulk(es, actions)
