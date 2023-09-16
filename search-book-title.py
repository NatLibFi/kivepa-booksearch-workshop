import sys
import warnings

from elasticsearch import Elasticsearch


if len(sys.argv) > 1:
    bt = sys.argv[1]
else:
    print("no book given")

# Connect to Elasticsearch
# es_url = "http://localhost:9200"
es_url = "https://kvp-2023-workshop-elasticsearch.apps.kk-test.k8s.it.helsinki.fi:443"
es = Elasticsearch(es_url)


size = 20
resp = es.search(
    index="books",
    query={"match": {"title": {"query": bt, "operator": "and"}}},
    size=size,
)
if resp["hits"]["total"]["value"] >= size:
    warnings.warn(
        f'Number of matches {resp["hits"]["total"]["value"]}'
        f" exceeds search size {size}."
    )
print(f'Number of results: {resp["hits"]["total"]["value"]}')
for hit in resp["hits"]["hits"]:
    book = hit["_source"]
    print(f'Title: {book["title"]}')
    print(f'ISBN: {book["isbn"]}')
    print(f'Labels A: {book["subjects-a-labels"]}')
    print(f'Labels B: {book["subjects-b-labels"]}')
    print('---')