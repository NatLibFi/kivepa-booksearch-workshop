# kvp-2023 workshop

Commands to set up:

    python3 -m venv venv
    source venv/bin/activate
    pip install flask elasticsearch requests
    docker run --rm --net elastic --name es-node01 -p 9200:9200 -p 9300:9300 -e "xpack.security.enabled=false" -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:8.9.0

    # curl -X DELETE "localhost:9200/books"  # Delete existing index
    zcat ks-bib.json.gz | time python import-to-es.py  # Takes 70 secs for 100 books
    python search-all.py

    python initialize-sqlite3.py

    flask run --debug
