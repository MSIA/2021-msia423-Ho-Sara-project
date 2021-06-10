# WikiNews

Author: Sara Ho

QA: Haozhang Deng

<!-- toc -->

- [Project charter](#project-charter)
- [Directory structure](#directory-structure)
- [1. Pre-requisites](#1-pre-requisites)
    + [1.1 Environmental Variables](#11-Environmental-Variables)
    + [1.2 Docker Builds](#12-Docker-Builds)
- [2. Pipeline](#2-pipeline)
    + [2.1 Load new data via API](#21-load-new-data-via-api)
    + [2.2 Run algorithm](#22-run-algorithm)
    + [2.3 Ingest to database](#23-ingest-to-database)
- [3. Run the Flask app](#3-run-the-flask-app)
- [4. Testing](#4-testing)
<!-- tocstop -->

# Project charter

The fast-paced nature of online news delivery and social media means that readers today regularly ingest news headlines without meaningful context. This app offers an alternative way to understand the news by providing context through Wikipedia articles.

## Vision

To display daily news content and suggest Wikipedia articles that are relevant to them. Users can read the news in a way is engaging and interactive, but with minimal bias and misinformation.

## Mission

The headlines and news descriptions [https://newsapi.org/](https://newsapi.org/). Spacy's pretrained [Named Entity Recognition](https://spacy.io/api/entityrecognizer) (NER) tool can be used to extract names, organizations, locations, phrases, etc. from a news description. The resulting entities/topics can then be used to query wikipedia pages using the wikipedia API.

Given a search query, the Wikipedia API can return the most relevant articles. 

For example, here is an April 4th headline: `"GMC's newly-unveiled Hummer EV SUV is 830HP of electric 'supertruck'"`. Using NER entities to search Wikipedia, these articles are suggested (most recent revision times are also shown).

```
GMC (automobile)

GMC Hummer EV

HP EliteBook
```

The first two articles are relevant, but the third is not. Irrelevant articles can be removed if they fail to meet a similarity metric threshhold.

- [News API](https://newsapi.org/v2/top-headlines?)
- [Wikipedia API](https://en.wikipedia.org/w/api.php)

## Success criteria

**Prediction metric:**

After searching Wikipedia for the topic(s), the app should identify whether the top result is relevant to the news article. A number of similarity metrics are tested before determining the optimal metric and threshhold.

**Business outcome:**

Ideally the deployed app would track whether a user clicks on the drop-downs to the Wikipedia articles. Business success can be measured based on a ratio of the number of internal link clicks versus overall visits to the web app. This is possible to measure but outside the scope of the project.

## Directory structure 

```
├── README.md                         <- You are here
├── api
│   ├── static/                       <- CSS files that remain static
│   ├── templates/                    <- HTML that is templated and changes based on a set of inputs
│   ├── boot.sh                       <- Start up script for launching app in Docker container.
│   ├── Dockerfile                    <- Dockerfile for building image to run app 
│
├── config                            <- Directory for configuration files 
│   ├── local/                        <- Directory for keeping environment variables and other local configurations that *do not sync** to Github 
│   ├── logging/                      <- Configuration of python loggers
│   ├── yaml                          <- YAML configurations for scripts in /src
│   │   ├── algorithm.yaml
│   │   ├── db.yaml
│   │   ├── load_news.yaml
│   │   ├── load_wiki.yaml
│   ├── flaskconfig.py                <- Configurations for Flask API 
│
├── data                              
│   ├── sample/                       <- Folder that contains sample data (static; syncs to GitHub)
│   │   ├── news-entries.csv
│   │   ├── wiki-entries.csv
│   ├── daily/                        <- Folder that contains updated daily data (dynamic; does not sync to GitHub)
│
├── deliverables/
│   ├── wikinews-06-07-21.pdf         <- Presentation explaining the project
│
├── notebooks/
│   ├── algorithm.ipynb               <- Notebook which evaluates metrics relating to the algorithm
│   
├── src/                              <- Source data for the project 
│   ├── algorithm.py                  <- Algorithm to filter out irrelevant results
│   ├── db.py                         <- Functionality to create database and ingest new data
│   ├── load_news.py                  <- Functionality to make calls to news API and save cleaned data into tables
│   ├── load_wiki.py                  <- Functionality to make calls to wiki API, match news to wikipedia pages, and save data into tables
│   ├── s3.py                         <- Function to load local files to s3
│
├── test/                             <- Files necessary for running tests
│   ├── test_algorithm.py
│   ├── test_db.py
│   ├── test_load_news.py
│   ├── test_load_wiki.py
│
├── app.py                            <- Flask wrapper for displaying the filtered data 
├── Dockerfile_make                   <- Dockerfile for running Makefile pipeline
├── Makefile                          <- Makefile for running pipeline to acquire data, apply algorithm, and ingest to db
├── run.py                            <- Simplifies the execution the src scripts  
├── requirements.txt                  <- Python package dependencies 
├── sample.sh                         <- Script which allows pipeline to be run without APIs; see section 2.1
```

## 1. Pre-requisites

### 1.1 Environmental Variables:

Here is the recommended setup:
```
export NEWS_API_KEY=<MY_NEWS_API_KEY>
export AWS_ACCESS_KEY_ID=<MY_AWS_ACCESS_KEY_ID>
export AWS_SECRET_ACCESS_KEY=<MY_AWS_SECRET_ACCESS_KEY>
export S3_BUCKET=<MY_S3_BUCKET>
export ENGINE_STRING=<host>://<user>:<password>@<endpoint>:<port>/<database>
```

 - Without a valid `NEWS_API_KEY`, `load_new` commands will not run. You can generate one for free at https://newsapi.org/ and add it to the environment.

 - Without a valid `S3_BUCKET`, `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, the data will still be saved locally according to the path(s) set in the Makefile, but they will not be saved to S3.

 - Without a valid `ENGINE_STRING`, a database will be created at `sqlite:///data/entries.db` and used throughout the pipeline.

 - Without obtaining the current date using `export DATE=$(date +"%m-%d-%y")`, the rest of the pipeline will use `06-08-21`, which is the date of the data in `data/sample`.

### 1.2 Docker builds:

`Dockerfile_make` runs entrypoint `make` to allow using the Makefile to aquire data, run the algorithm, and ingest to RDS
```bash
docker build -f Dockerfile_make -t make_wikinews .
```

`app/Dockerfile` runs the app; it can also be used for deployment via ECS
```bash
docker build -f app/Dockerfile -t wikinews .
```

## 2. Pipeline

At each point, intermediate data are saved to S3, so `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are required in addition to other ad-hoc environmental variables.

### 2.1 Load new data via API

```bash
make data
```

or equivalently through Docker:
```bash
docker run \
    --mount type=bind,source="$(pwd)",target=/app/ \
    -e AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY \
    -e S3_BUCKET \
    -e NEWS_API_KEY \
make_wikinews data
```

### 2.2 Run algorithm

```bash
make algorithm
```

or equivalently through Docker:
```bash
docker run \
    --mount type=bind,source="$(pwd)",target=/app/ \
    -e AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY \
    -e S3_BUCKET \
make_wikinews algorithm
```

### 2.3 Ingest to database

*In development, an AWS RDS database was used; it required access to Northwestern's VPN. If using a similar set-up, please make sure to connect to the required VPN*

```bash
make algorithm
```

or equivalently through Docker:
```bash
docker run \
    --mount type=bind,source="$(pwd)",target=/app/ \
    -e AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY \
    -e S3_BUCKET \
    -e ENGINE_STRING \
make_wikinews database
```

[Optional]. If using MySQL, access SQL commands via Docker:
```bash
docker run -it --rm \
    mysql:5.7.33 \
    mysql \
    -h$<host> \
    -u$<user> \
    -p$<database>
```

If using a database which does not support utf8 characters (which may show up especially in the Wikipedia data), you can configure it this way. It is recommended that this be done when the database is NOT in use through the app.

```sql
ALTER DATABASE `<database>` DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci;

ALTER TABLE wiki CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci;
ALTER TABLE news CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci;
```

## 3. Run the Flask app 

`config/flaskconfig.py` holds the configurations for the Flask app.

```bash
python app.py
```

or equivalently through Docker:
```bash
docker run 
    -p 5000:5000 
    -e ENGINE_STRING
    --name app
wikinews
```

If no `ENGINE_STRING` is provided, the database will default to the one created locally at `sqlite:///data/entries.db`. 

You should now be able to access the app at http://0.0.0.0:5000/ in your browser.

## 4. Testing

From within the Docker container, the following command should work to run unit tests when run from the root of the repository: 

```bash
python -m pytest
``` 

or equivalently through Docker:
```bash
 docker run wikinews -m pytest
```
 