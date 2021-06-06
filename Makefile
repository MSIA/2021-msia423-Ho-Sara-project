
s3: s3_labeled s3_sample s3_daily 
update: load_news load_wiki s3_daily
launch: join filter create_db ingest

date = $(shell date +"%m-%d-%y")
s3_bucket = s3://2021-msia-423-ho-sara
daily_news = data/daily/${date}-news-entries.csv
daily_wiki = data/daily/${date}-wiki-entries.csv
daily_joined = data/daily/${date}-joined.csv
daily_filtered = data/daily/${date}-filtered.csv

log:
	echo ${s3_bucket}

s3_labeled: data/labeled/labeled.csv
	python3 run.py s3 --input=data/labeled/labeled.csv --s3_path=${s3_bucket}

s3_sample: data/sample/news-entries.csv data/sample/wiki-entries.csv
	python3 run.py s3 --input1=data/sample/news-entries.csv --input2=data/sample/wiki-entries.csv --s3_path=${s3_bucket}

s3_daily: ${daily_news} ${daily_wiki}
	python3 run.py s3 --input1=${daily_news} --input2=${daily_wiki} --s3_path=${s3_bucket}

${daily_news}: config/load.yaml
	python3 run.py load_news --config=config/load.yaml --output=${daily_news}

load_news: ${daily_news}

${daily_wiki}: config/load.yaml ${daily_news}
	python3 run.py load_wiki --config=config/load.yaml --input=${daily_news} --output=${daily_wiki}

load_wiki: ${daily_wiki}

${daily_joined}: ${daily_news} ${daily_wiki}
	python3 run.py join --input1=${daily_news} --input2=${daily_wiki} --output=${daily_joined} --s3_path=${s3_bucket}

join: ${daily_joined}

${daily_filtered}: config/algorithm.yaml ${daily_joined}
	python3 run.py filter --config=config/algorithm.yaml --input=${daily_joined} --output=${daily_filtered} --s3_path=${s3_bucket}

filter: ${daily_filtered}

create_db:
	python3 run.py create_db

ingest: ${daily_filtered} config/db.yaml
	python3 run.py ingest --input=${daily_filtered} --s3_path=${s3_bucket} --config=config/db.yaml
