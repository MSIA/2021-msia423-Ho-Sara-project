
make NEWS_API_KEY="${NEWS_API_KEY}" target
DAILY_DIR=data/daily

remove_old:
	rm -rf data/daily/*.csv

data/daily/news-entries.csv: config/config.yaml
	python3 run.py load_news --config=config/config.yaml --output=data/daily/news-entries.csv

load_news: data/daily/news-entries.csv

data/daily/wiki-entries.csv: data/daily/news-entries.csv
	python3 run.py load_wiki --input=data/daily/news-entries.csv --output=data/daily/wiki-entries.csv

load_wiki: data/daily/wiki-entries.csv

data/joined.csv: ${DAILY_DIR}/news-entries.csv ${DAILY_DIR}/wiki-entries.csv
	python3 run.py join --input1=${DAILY_DIR}/news-entries.csv --input2=${DAILY_DIR}/wiki-entries.csv --output=data/joined.csv

join: data/joined.csv

data/filtered.csv:
	python3 run.py filter --output=data/filtered.csv

filter: data/filtered.csv

create_db:
	python3 run.py create_db

ingest: data/joined.csv
	python3 run.py ingest --input=data/joined.csv

update: remove_old load_news load_wiki 
launch: join filter create_db ingest
