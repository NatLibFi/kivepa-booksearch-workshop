from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")


resp = es.search(index="books", query={"match_all": {}})
print("Got %d Hits:" % resp['hits']['total']['value'])
for hit in resp['hits']['hits']:
    print(hit)
