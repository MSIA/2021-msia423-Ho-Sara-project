
s3_bucket = $(or ${S3-BUCKET},2021-msia-423-ho-sara)

# if no API KEY is in environment, the sample data from 06-08-21 is used
today = $(if ${NEWS_API_KEY},$(date +"%m-%d-%y"),06-08-21)
data_path = $(if ${NEWS_API_KEY},data/daily,data/sample)

daily_news = ${data_path}/${today}-news-entries.csv
daily_wiki = ${data_path}/${today}-wiki-entries.csv
daily_joined = ${data_path}/${today}-joined.csv
daily_predict = ${data_path}/${today}-predict.csv
daily_filtered = ${data_path}/${today}-filtered.csv

s3: s3_labeled s3_sample 

data: load_news load_wiki s3_daily

algorithm: join predict filter

database: create_db ingest

s3_labeled:
	python3 run.py s3 --input=data/labeled/labeled.csv --s3_path=${s3_bucket}

s3_sample:
	python3 run.py s3 --input1=data/sample/06-08-21-news-entries.csv --input2=data/sample/06-08-21-wiki-entries.csv --s3_path=${s3_bucket}

s3_daily:
	python3 run.py s3 --input1=${daily_news} --input2=${daily_wiki} --s3_path=${s3_bucket}

load_news: config/load_news.yaml
	python3 run.py load_news --config=config/yaml/load_news.yaml --output=${daily_news}

load_wiki: config/load_wiki.yaml ${daily_news}
	python3 run.py load_wiki --config=config/yaml/load_wiki.yaml --input=${daily_news} --output=${daily_wiki}

join: ${daily_news} ${daily_wiki}
	python3 run.py join --input1=${daily_news} --input2=${daily_wiki} --output=${daily_joined}

predict: ${daily_joined}
	python3 run.py predict --config=config/yaml/algorithm.yaml --input=${daily_joined} --output=${daily_predict}

filter: ${daily_predict}
	python3 run.py filter --config=config/yaml/algorithm.yaml --input=${daily_predict} --output=${daily_filtered}

create_db:
	python3 run.py create_db

ingest: ${daily_filtered}
	python3 run.py ingest --input=${daily_filtered} --s3_path=${s3_bucket} --config=config/yaml/db.yaml

test:
	python3 -m pytest

.PHONY: test