# Booksearch application for workshop at Kirjastoverkkopäivät 2023
An application which is planned to be used at the workshop of automated indexing of fiction books at Kirjastoverkkopäivät 2023.

Developed with help from ChatGPT.

## Set up local environment
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

## Get subjects for books from Annif
    time python get-annif-subjects.py  # Takes ~5 hours for all books

## Local development
### Set up Elasticsearch and indices
    docker run --rm --net elastic --name es-node01 -p 9200:9200 -p 9300:9300 -e "xpack.security.enabled=false" -e "discovery.type=single-node" -v es-data:/usr/share/elasticsearch/data docker.elastic.co/elasticsearch/elasticsearch:8.9.1

    # curl -X DELETE "localhost:9200/books"  # Delete existing index
    time python import-books-to-es.py &> import-books.out  # Takes 5 min for 1000 books, 15 min for 4000 books, etc.

    # curl -X DELETE "localhost:9200/autocomplete"  # Delete existing index
    python create-autocomplete-index.py
#### Alternatively use Elasticsearch running in OpenShift
    export ELASTICSEARCH_URL=https://kvp-2023-workshop-elasticsearch.apps.kk-test.k8s.it.helsinki.fi:443
### Start application
    flask run --debug
    # gunicorn app:app  # Alternatively use gunicorn

## Deploy in OpenShift
The application will be publicly available at https://kvp-2023-workshop.ext.kk-test.k8s.it.helsinki.fi/

The deploykey for the private repository containing the Dockerfile needs to be in place.
### Install/update application
    helm upgrade --install kvp-2023-workshop helm-charts/
    # oc start-build kvp-2023-workshop-app  # Rebuild Docker image

### Create indices

    # curl -X DELETE "https://kvp-2023-workshop-elasticsearch.apps.kk-test.k8s.it.helsinki.fi:443/books"  # Delete old
    # curl -X DELETE "https://kvp-2023-workshop-elasticsearch.apps.kk-test.k8s.it.helsinki.fi:443/autocomplete"  # Delete old

    time python import-books-to-es.py https://kvp-2023-workshop-elasticsearch.apps.kk-test.k8s.it.helsinki.fi:443 &> import-books.out
    python create-autocomplete-index.py https://kvp-2023-workshop-elasticsearch.apps.kk-test.k8s.it.helsinki.fi:443

### Access app container for debugging etc.
     oc rsh deployment/kvp-2023-workshop-app python -c "from elasticsearch import Elasticsearch; es = Elasticsearch('http://kvp-2023-workshop-elasticsearch:9200'); print(es.indices.get(index='*'))"

## Elasticsearch queries
    curl http://localhost:9200/_aliases
    curl http://localhost:9200/books?pretty
    curl http://localhost:9200/books/_count
    # Note: Search returns only 10 results by default
    curl localhost:9200/books/_search?pretty -H "Content-Type: application/json" -d '{
      "query": {
        "match": {
          "title": "Kissa"
        }
      }
    }'



## TODO How to set up the Apache Jena for data preprocessing
Needed for running SPARQL query to process the file [kirjasampo-bib.json-ld.gz](https://github.com/NatLibFi/Annif-corpora-restricted/blob/master/kirjasampo/kirjasampo-bib.json-ld.gz).

1. Download (latest) Jena from https://downloads.apache.org/jena/binaries/ and unpack it
2. cd to the directory
3. Start Jena `./fuseki-server`
4. In a web browser navigate to http://localhost:3030/#/
5. ?
