# WikiNews

Author: Sara Ho

QA: Haozhang Deng

<!-- toc -->

- [Project charter](#project-charter)
- [Directory structure](#directory-structure)
- [Running the app](#running-the-app)
  * [1. Initialize the database](#1-initialize-the-database)
    + [Load new data via API](#Load-new-data-via-API)
    + [Set up local database](#Set-up-local-database)
    + [Set up database via engine](#Set-up-database-via-engine)
    + [Load data into s3](#Load-data-into-s3)
    + [Set up database in Docker](#Set-up-database-in-Docker)
  * [2. Configure Flask app](#2-configure-flask-app)
  * [3. Run the Flask app](#3-run-the-flask-app)
- [Running the app in Docker](#running-the-app-in-docker)
  * [1. Build the image](#1-build-the-image)
  * [2. Run the container](#2-run-the-container)
  * [3. Kill the container](#3-kill-the-container)

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
│   ├── Dockerfile_update             <- Dockerfile for running makefile to update and ingest data  
│
├── config                            <- Directory for configuration files 
│   ├── local/                        <- Directory for keeping environment variables and other local configurations that *do not sync** to Github 
│   ├── logging/                      <- Configuration of python loggers
│   ├── flaskconfig.py                <- Configurations for Flask API 
│   ├── algorithm.yaml                <- Configurations for src/algorithm.py 
│   ├── load.yaml                     <- Configurations for src/load.py 
|
├── data                              
│   ├── sample/                       <- Folder that contains sample data (static; syncs to GitHub)
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
│   ├── load.py                       <- Functionality to make calls to APIs, match news to wikipedia pages, and save data into tables
│   ├── s3.py                         <- Function to load local file to s3
│
├── test/                             <- Files necessary for running tests
│   ├── test_db.py
|
├── Makefile 
├── app.py                            <- Flask wrapper for displaying the filtered data 
├── run.py                            <- Simplifies the execution the src scripts  
├── requirements.txt                  <- Python package dependencies 
```

## 1. Pre-requisites

## Environmental Variables:

Without an News API key, `load_new` commands will not run. You can generate one for free at https://newsapi.org/ and add it to the environment.
`export NEWS_API_KEY=<MY_KEY_HERE>`
Otherwise, you can skip loading new data. The rest of the commands will default to using existing data in local path `./data/sample`

## Docker builds:

Runs entrypoint `make` to allow using the Makefile to aquire data, run the algorithm, and ingest to RDS
```
docker build -f Dockerfile_make -t make_wikinews .
```

Runs the app; can also be used for deployment via ECS
```
docker build -f app/Dockerfile -t wikinews .
```

## 2. Pipeline

At each point, intermediate data are saved to S3, so `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are required in addition to other ad-hoc environmental variables.

## Load new data via API.

```
make data
```
or equivalently through Docker:
```
docker run \
    --mount type=bind,source="$(pwd)",target=/app/ \
    -e AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY \
    -e NEWS_API_KEY \
make_wikinews data
```

## Run algorithm

```
make algorithm
```
or equivalently through Docker:
```
docker run \
    --mount type=bind,source="$(pwd)",target=/app/ \
    -e AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY \
make_wikinews algorithm
```

## Ingest to database

```
make algorithm
```
or equivalently through Docker:
```
docker run \
    --mount type=bind,source="$(pwd)",target=/app/ \
    -e AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY \
    -e ENGINE_STRING \
make_wikinews ingest
```

If no `ENGINE_STRING` provided, the database will be created locally at `sqlite:///data/entries.db`. 

## Access database [Optional]

If using MySQL, access interface via docker,
```bash
docker run -it --rm \
    mysql:5.7.33 \
    mysql \
    -h${MYSQL_HOST} \
    -u${MYSQL_USER} \
    -p${MYSQL_DB}
```

## 3. Run the Flask app 

`config/flaskconfig.py` holds the configurations for the Flask app.

```bash
python app.py
```
or equivalently through Docker:
```bash
docker run \
-p 5000:5000 \
-e ENGINE_STRING \
wikinews app.py
```

You should now be able to access the app at http://0.0.0.0:5000/ in your browser.

# Testing

From within the Docker container, the following command should work to run unit tests when run from the root of the repository: 

```bash
python -m pytest
``` 

or equivalently through Docker:
```bash
 docker run wikinews -m pytest
```
 