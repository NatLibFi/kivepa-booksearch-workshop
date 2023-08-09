from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")


resp = es.search(index="books", query={"match_all": {}})
print("Got %d Hits:" % resp['hits']['total']['value'])
for hit in resp['hits']['hits']:
    print(hit)
    # print("%(timestamp)s %(author)s: %(text)s" % hit["_source"])



# resp = es.search(
#     index="movies",
#     query={
#         "bool": {
#             "must": {
#                 "match_phrase": {
#                     "cast": "jack nicholson",
#                 }
#             },
#             "filter": {
#                 "bool": {"must_not": {"match_phrase": {"director": "roman polanski"}}}
#             },
#         },
#     },
# )
# print(resp.body)
