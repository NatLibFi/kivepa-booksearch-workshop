# THIS REPOSITORY HAS BEEN ARCHIVED

# Booksearch application for workshop at Kirjastoverkkopäivät 2023
An application which was used at the [workshop of automated indexing of fiction books at Kirjastoverkkopäivät 2023](https://www.kansalliskirjasto.fi/fi/kirjastoverkkopaivat-2023-torstain-tyopajat#klo-9-12-tp3-kaunokirjallisuuden-automaattinen-sisallonkuvailu).

Developed with help by ChatGPT.

See the article about the workshop:
_Lehtinen M., Inkinen J. & Suominen O. (2023). Kaunokirjallisuuden automaattinen kuvailu – Tarinaluotsi vs. Juonenjyvä. Tietolinja, 2023(2)._
Pysyvä osoite: https://urn.fi/URN:NBN:fi-fe20231218155441

## Set up local environment
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

## Get subjects for books from Annif
    time python get-annif-subjects.py

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
The application will be publicly available at the address given in [route template](https://github.com/juhoinkinen/kivepa-booksearch-workshop/blob/06f2e9ada71e73b90c993270e44058fc1067c8c7/helm-charts/templates/route.yaml#L10).

If this repository is private a deploykey needs to be in place as a secret in Openshift.

### Install/update application
    helm upgrade --install kvp-2023-workshop helm-charts/
    # oc start-build kvp-2023-workshop-app  # Rebuild Docker image

### Create indices

    # curl -X DELETE "https://kvp-2023-workshop-elasticsearch.apps.kk-test.k8s.it.helsinki.fi:443/books"  # Delete old
    # curl -X DELETE "https://kvp-2023-workshop-elasticsearch.apps.kk-test.k8s.it.helsinki.fi:443/autocomplete"  # Delete old

    time python import-books-to-es.py https://kvp-2023-workshop-elasticsearch.apps.kk-test.k8s.it.helsinki.fi:443 &> import-books.out
    python create-autocomplete-index.py https://kvp-2023-workshop-elasticsearch.apps.kk-test.k8s.it.helsinki.fi:443

### Database resetting and copying to local machine for analysis

    # oc rsh deployment/kvp-2023-workshop-app rm sqlite3-data/database.db  # Delete
    oc rsync <pod-name>:sqlite3-data/ ./os-sqlite3-data

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
