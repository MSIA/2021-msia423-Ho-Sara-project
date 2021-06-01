
make NEWS_API_KEY="${NEWS_API_KEY}" target

remove_old:
	rm -rf data/daily/*.csv

data/daily/news-entries.csv: config/config.yaml
	python3 run.py load_news --config=config/config.yaml --output=data/daily/news-entries.csv

load_news: data/daily/news-entries.csv

data/daily/wiki-entries.csv: data/daily/news-entries.csv
	python3 run.py load_wiki --input=data/daily/news-entries.csv --output=data/daily/wiki-entries.csv

load_wiki: data/daily/wiki-entries.csv

data/filtered.csv:
	python3 run.py filter --output=data/filtered.csv

filter: data/filtered.csv

create_db:
	python3 run.py create_db

ingest: data/filtered.csv
	python3 run.py ingest --input=data/filtered.csv

daily_update: remove_old load_news load_wiki filter create_db ingest
