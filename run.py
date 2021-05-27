import os
import argparse
from datetime import datetime
from datetime import date
import unicodedata
import logging
import logging.config

import pandas as pd
import boto3
import botocore

from src.load_data import load_wiki, load_news
from src.add_entries import WikiNewsManager, create_db
from config.flaskconfig import SQLALCHEMY_DATABASE_URI

NEWS_API_KEY = os.environ.get('NEWS_API_KEY')

logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s', level=logging.DEBUG)
logging.getLogger("botocore").setLevel(logging.ERROR)
logging.getLogger("s3transfer").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("boto3").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("aiobotocore").setLevel(logging.ERROR)
logging.getLogger("s3fs").setLevel(logging.ERROR)

logging.config.fileConfig("config/logging/local.conf",
                          disable_existing_loggers=False)
logger = logging.getLogger(__name__)


def upload_files_to_s3(local_path, s3path):
    """ Upload local files to s3 """

    s3bucket = s3path.replace('s3://', '')

    s3 = boto3.resource("s3")
    bucket = s3.Bucket(s3bucket)

    files = os.listdir(local_path)
    files = [file for file in files if '.csv' in file]
    for file in files:
        try:
            bucket.upload_file(f'{local_path}/{file}', f'raw/{file}')
        except botocore.exceptions.NoCredentialsError:
            logger.error('Please provide AWS credentials via AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env variables.')
        else:
            logger.info('Data uploaded to %s', {s3path} + '/raw/' + {file})


def remove_accents(s):
    return unicodedata.normalize('NFD', s)


def add_wiki_file(file):
    wiki_table = pd.read_csv(f'{args.local_path}/{file}')
    wiki_table = wiki_table.fillna('')

    wiki_table['title'] = wiki_table['title'].apply(remove_accents)
    # when accents are removed, the primary keys may no longer be unique
    wiki_table = wiki_table.drop_duplicates(['news_id', 'entity', 'title'])

    file_date = ('-').join(file.split('-')[0:3])
    file_date = datetime.strptime(file_date, '%b-%d-%Y')

    for _, row in wiki_table.iterrows():
        news_id, entity, label, title, category, revised, url, wiki, image = row
        tm.add_wiki(file_date, news_id, entity, label,
                    title, category, revised,
                    url, wiki, image)
    logger.info(f"data in {file} added to 'wiki' table")


def add_news_file(file):
    news_table = pd.read_csv(f'{args.local_path}/{file}')
    news_table = news_table.fillna('')
    file_date = ('-').join(file.split('-')[0:3])
    file_date = datetime.strptime(file_date, '%b-%d-%Y')

    for _, row in news_table.iterrows():
        news_id, news, content, img, url = row
        tm.add_news(file_date, news_id, news, content, img, url)
    logger.info(f"data in {file} added to 'news' table")


if __name__ == '__main__':

    # Add parsers for both creating a database and adding entries to it
    parser = argparse.ArgumentParser(description="Create and/or add data to database")
    subparsers = parser.add_subparsers(dest='subparser_name')

    # Sub-parser for creating a database
    sb_create = subparsers.add_parser('create_db', description="Create database")
    sb_create.add_argument("--engine_string", default='sqlite:///data/entries.db',
                           help="SQLAlchemy connection URI for database")

    # Sub-parser for ingesting new data
    sb_ingest = subparsers.add_parser('ingest', description="Add data to database")
    sb_ingest.add_argument("--engine_string", default='sqlite:///data/entries.db',
                           help="SQLAlchemy connection URI for database")
    sb_ingest.add_argument("--local_path", default='./data/sample',
                           help="Filepath for local data for database to ingest")

    # Sub-parser to load new data into local ./data folder
    sb_load = subparsers.add_parser('load_new', description="Query new data from APIs and save locally")

    # Sub-parser to load data from local path into s3
    sb_s3 = subparsers.add_parser('load_s3', description="Describe where local data is")
    sb_s3.add_argument('--s3path', default='s3://2021-msia-423-ho-sara',
                       help="If used, will load data to s3")
    sb_s3.add_argument('--local_path', default='./data/sample',
                       help="Where to load data to in S3")

    args = parser.parse_args()
    sp_used = args.subparser_name

    if sp_used == 'create_db':
        create_db(args.engine_string)

    elif sp_used == 'ingest':
        tm = WikiNewsManager(engine_string=args.engine_string)

        for file in os.listdir(args.local_path):

            if 'wiki-entries' in file:
                add_wiki_file(file)

            elif 'news-entries' in file:
                add_news_file(file)

            tm.close()

    elif sp_used == 'load_new':
        # by default, this will save new csv files into ./data
        news = load_news(NEWS_API_KEY)
        load_wiki(news)

    elif sp_used == 'load_s3':
        upload_files_to_s3(args.local_path, args.s3path)

    else:
        parser.print_help()
