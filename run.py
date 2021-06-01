import os
import argparse
from datetime import datetime
from datetime import date
import unicodedata
import logging
import logging.config
import yaml

import pandas as pd
import boto3
import botocore
import spacy
from spacy import displacy

from src.load_data import load_wiki, load_news
from src.add_entries import WikiNewsManager, create_db
from src.filter_algo import filter_data, join_data

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


def render_text(text, entities):
    entity_locs = []
    for ent in entities:
        if ' (organization)' in ent:
            ent = ent.replace(' (organization)', '')
        start = text.find(ent)
        end = start + len(ent)
        entity_locs.append({'start': start, 'end': end, 'label': ''})

    colors = {"": "linear-gradient(90deg, #a2dff0, #b1d3ae)"}
    options = {"ents": [""], "colors": colors}

    doc = [{"text": text,
            "ents": entity_locs,
            "title": None}]
    return displacy.render(doc, style="ent", jupyter=False, manual=True, options=options)


def ingest_wiki(wiki_df, engine_string):
    """ ingest wiki dataframe """

    tm = WikiNewsManager(engine_string=engine_string)
    for _, row in wiki_df.iterrows():
        date, news_id, title, wiki, url, image = row
        tm.add_wiki(date, news_id, title, wiki, url, image)
    logger.info(f"{len(wiki_df)} rows added to 'wiki' table")
    tm.close()


def ingest_news(news_df, df, engine_string):
    """ ingest news dataframe """

    tm = WikiNewsManager(engine_string=engine_string)
    for _, row in news_df.iterrows():
        date, news_id, news, image, url = row
        entities = df.loc[df['news_id'] == news_id, 'entity'].values
        news_dis = render_text(news, entities)
        tm.add_news(date, news_id, news, news_dis, image, url)
    logger.info(f"{len(news_df)} rows  added to 'news' table")
    tm.close()


def ingest(file_path, engine_string):
    """after data is joined and filtered, ingest to database

    Args:
        df (obj `pandas.DataFrame`): output from filter_algo()
    """
    df = pd.read_csv(file_path)
    df = df.fillna('')

    # when accents are removed, the primary keys may no longer be unique
    df['title'] = df['title'].apply(remove_accents)
    df = df.drop_duplicates(['news_id', 'entity', 'title'])

    wiki_df = df[['date', 'news_id', 'title', 'wiki', 'wiki_url', 'wiki_image']].drop_duplicates()
    ingest_wiki(wiki_df, engine_string)

    news_df = df[['date', 'news_id', 'news', 'news_image', 'news_url']].drop_duplicates()
    ingest_news(news_df, df, engine_string)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Create and/or add data to database")
    parser.add_argument('step', help='Which step to run', choices=['load_news', 'load_wiki', 'filter', 'create_db', 'ingest'])
    parser.add_argument('--input', '-i', default=None, help='Path to input data')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--output', '-o', default=None, help='Path to save output CSV (optional, default = None)')
    parser.add_argument("--engine_string", default='sqlite:///data/entries.db',
                        help="SQLAlchemy connection URI for database")

    args = parser.parse_args()

    if args.config is not None:
        with open(args.config, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

        logger.info("Configuration file loaded from %s" % args.config)

    if args.input is not None:
        input = pd.read_csv(args.input)
        logger.info('Input data loaded from %s', args.input)

    if args.step == 'load_news':
        output = load_news(NEWS_API_KEY)

    elif args.step == 'load_wiki':
        output = load_wiki(args.input)

    elif args.step == 'filter':
        output = filter_data('data/daily')

    elif args.step == 'create_db':
        create_db(args.engine_string)

    elif args.step == 'ingest':
        ingest(args.input, args.engine_string)

    # else:
    #     test.run_tests(args)

    if args.output is not None:
        output.to_csv(args.output, index=False)
        logger.info("Output saved to %s" % args.output)

    # # Add parsers for both creating a database and adding entries to it
    # parser = argparse.ArgumentParser(description="Create and/or add data to database")
    # subparsers = parser.add_subparsers(dest='subparser_name')

    # # Sub-parser for creating a database
    # sb_create = subparsers.add_parser('create_db', description="Create database")
    # sb_create.add_argument("--engine_string", default='sqlite:///data/entries.db',
    #                        help="SQLAlchemy connection URI for database")

    # # Sub-parser for ingesting new data
    # sb_ingest = subparsers.add_parser('ingest', description="Add data to database")
    # sb_ingest.add_argument("--engine_string", default='sqlite:///data/entries.db',
    #                        help="SQLAlchemy connection URI for database")
    # sb_ingest.add_argument("--local_path", default='./data/sample',
    #                        help="Filepath for local data for database to ingest")

    # # Sub-parser to load new data into local ./data folder
    # sb_load = subparsers.add_parser('load_new', description="Query new data from APIs and save locally")
    # sb_load.add_argument('--local_path', default='./data/',
    #                      help="Load daily local data")

    # # Sub-parser to load data from local path into s3
    # sb_s3 = subparsers.add_parser('load_s3', description="Describe where local data is")
    # sb_s3.add_argument('--s3path', default='s3://2021-msia-423-ho-sara',
    #                    help="If used, will load data to s3")
    # sb_s3.add_argument('--local_path', default='./data/sample',
    #                    help="Where to load data to in S3")

    # args = parser.parse_args()
    # sp_used = args.subparser_name

    # if sp_used == 'create_db':
    #     create_db(args.engine_string)

    # elif sp_used == 'ingest':
    #     engine_string = args.engine_string
    #     df = join_data(args.local_path)
    #     df = filter_data(df)
    #     logger.info(df.columns)
    #     ingest(df, engine_string)

    # elif sp_used == 'load_new':
    #     # by default, this will save new csv files into ./data
    #     news = load_news(NEWS_API_KEY, args.local_path)
    #     load_wiki(news, n_results=1)

    # elif sp_used == 'load_s3':
    #     upload_files_to_s3(args.local_path, args.s3path)

    # else:
    #     parser.print_help()
