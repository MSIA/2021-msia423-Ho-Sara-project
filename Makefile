daily_update: build load_new load_s3 create_aws launch_app

build:
	docker build -f app/Dockerfile -t wikinews .

load_new:
	docker run \
		-e NEWS_API_KEY \
		-e AWS_ACCESS_KEY_ID \
		-e AWS_SECRET_ACCESS_KEY \
		-e PYTHONIOENCODING=utf-8 \
		wikinews run.py load_new --local_path ./data/daily

load_s3:
	docker run \
		-e NEWS_API_KEY \
		-e AWS_ACCESS_KEY_ID \
		-e AWS_SECRET_ACCESS_KEY \
		-e PYTHONIOENCODING=utf-8 \
		wikinews run.py load_s3 --local_path ./data/daily

# create_aws:
# 	docker run \
# 		-e AWS_ACCESS_KEY_ID \
# 		-e AWS_SECRET_ACCESS_KEY \
# 		wikinews run.py create_db \
# 		--engine_string=mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@${MYSQL_HOST}:${MYSQL_PORT}/${DATABASE_NAME}

launch_app:
	docker run \
		-p 5000:5000 wikinews app.py