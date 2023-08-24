# kvp-2023 workshop

## Set up locally
### Set up environment:
    python3 -m venv venv
    source venv/bin/activate
    pip install flask elasticsearch requests

### Set up Elasticsearch
    docker run --rm --net elastic --name es-node01 -p 9200:9200 -p 9300:9300 -e "xpack.security.enabled=false" -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:8.9.0

    # curl -X DELETE "localhost:9200/books"  # Delete existing index
    zcat ks-bib.json.gz | time python import-books-to-es.py  # Takes 5 min for 200 books
    # python search-all.py  # Show contents of "books" index

    # curl -X DELETE "localhost:9200/labels"  # Delete existing index
    python create-autocomplete-index.py

### Set up sqlite for storing results
    python initialize-sqlite3.py

### Start appliction
    flask run --debug
    # gunicorn app:app  # Alternatively use gunicorn

# How to set up the Apache Jena
Needed for running SPARQL query to process the file [kirjasampo-bib.json-ld.gz](https://github.com/NatLibFi/Annif-corpora-restricted/blob/master/kirjasampo/kirjasampo-bib.json-ld.gz).

1. Download (latest) Jena from https://downloads.apache.org/jena/binaries/ and unpack it
2. cd to the directory
3. Start Jena `./fuseki-server`
4. In a web browser navigate to http://localhost:3030/#/
5. ?
