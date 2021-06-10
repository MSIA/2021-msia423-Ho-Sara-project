"""Orchestration script

runs an arg parser which allows for the following steps:
load_news: run API for news data
load_wiki: run API for wiki data
join: prep data for filtering
filter: remove irrelevant matches
create_db: prep database for new data
ingest: ingest database with new data
s3: load any input into s3

this script is designed to work with ./Makefile
"""

import os
import argparse
import logging
import logging.config

import yaml
import pandas as pd

from src.db import create_db, ingest
from src.load_news import load_news
from src.load_wiki import load_wiki
from src.algorithm import filter_data, join_data, predict_data
from src.s3 import upload

logging.config.fileConfig("config/logging/local.conf",
                          disable_existing_loggers=False)
logger = logging.getLogger(__name__)
logging.getLogger("s3fs").setLevel(logging.WARNING)


def handle_input_path(input_path, s3_path=None):
    """handle inputs for various steps in the arg parser"""

    if s3_path is not None:
        logger.info('Adding s3 path to input path')
        input_path = 's3://' + s3_path + '/' + input_path

    if input_path is not None:
        try:
            input_data = pd.read_csv(input_path)
            logger.debug('read %i lines of data', len(input_data))
            return input_data
        except FileNotFoundError:
            logger.error("File not found at path %s", input_path)
        except pd.errors.EmptyDataError:
            logger.error("No data")
        except pd.errors.ParserError:
            logger.error("Parse error")
    return None


def handle_engine_string(in_engine_string):
    """handle engine strings for various steps in the arg parser"""

    if in_engine_string is not None:
        engine_string = args.engine_string
        logger.info('using filepath sqlite:///data/entries.db as engine string')
    elif os.environ.get('ENGINE_STRING') is not None:
        engine_string = os.environ.get('ENGINE_STRING')
        logger.info('using env variable $ENGINE_STRING to connect to db')
    else:
        engine_string = 'sqlite:///data/entries.db'
        logger.info('using filepath sqlite:///data/entries.db as engine string')
    return engine_string


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Create and/or add data to database")
    parser.add_argument('step',
                        help='Which step to run',
                        choices=['load_news', 'load_wiki', 'filter',
                                 'create_db', 'join', 'predict', 'ingest', 's3'])

    parser.add_argument('--input', '-i', default=None,
                        help='Path to input data')
    parser.add_argument('--input1', default=None,
                        help='Path to input data')
    parser.add_argument('--input2', default=None,
                        help='Path to input data')

    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--output', '-o', default=None,
                        help='Path to save output CSV (default = None)')

    parser.add_argument("--engine_string",
                        help="connection URI for database")
    parser.add_argument("--s3_path",
                        help="s3 path")

    args = parser.parse_args()

    if args.config is not None:
        with open(args.config, 'r') as conf_file:
            conf = yaml.load(conf_file, Loader=yaml.FullLoader)

    if args.step == 'load_news':
        if conf is None:
            logger.error("yaml configuration file required for load_news()")
        else:
            output = load_news(conf,
                               source_words=conf['source_words'])

        if args.output is not None and args.s3_path is not None:
            upload(args.output, args.s3_path)
            logger.info("Output saved remotely to s3://%s", args.s3_path)

    elif args.step == 'load_wiki':
        if conf is None:
            logger.error("yaml configuration file required for load_wiki()")
        else:
            data = handle_input_path(args.input)
            output = load_wiki(data,
                               query_conf=conf['wiki_query'],
                               content_conf=conf['wiki_content'],
                               stop_spacy=conf['stop_spacy'],
                               spacy_model=conf['spacy_model'],
                               stop_categories=conf['stop_categories'],
                               stop_phrases=conf['stop_phrases'],
                               n_results=conf['n_results'])

        if args.output is not None and args.s3_path is not None:
            upload(args.output, args.s3_path)
            logger.info("Output saved remotely to s3://%s", args.s3_path)

    elif args.step == 'join':
        wiki_df = handle_input_path(args.input1, args.s3_path)
        news_df = handle_input_path(args.input2, args.s3_path)
        output = join_data(wiki_df, news_df)

    elif args.step == 'predict':
        if conf is None:
            logger.error("yaml configuration file required for predict()")
        data = handle_input_path(args.input)
        output = predict_data(data, conf)

    elif args.step == 'filter':
        data = handle_input_path(args.input)
        output = filter_data(data)

    elif args.step == 'create_db':
        engine_string = handle_engine_string(args.engine_string)
        create_db(engine_string)

    elif args.step == 'ingest':
        if conf is None:
            logger.error("yaml configuration file required for ingest()")
        data = handle_input_path(args.input)
        engine_string = handle_engine_string(args.engine_string)
        ingest(data, conf, engine_string)

    elif args.step == 's3':
        if args.input is not None:
            upload(args.input, args.s3_path)
        if args.input1 is not None:
            upload(args.input1, args.s3_path)
        if args.input2 is not None:
            upload(args.input2, args.s3_path)

    if args.output is not None:
        output.to_csv(args.output, index=False)
        logger.info("Output saved locally to %s", args.output)
