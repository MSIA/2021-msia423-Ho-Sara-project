import os
import argparse
import logging
import logging.config
import yaml

import pandas as pd
import s3fs

from src.db import WikiNewsManager, create_db, ingest
from src.load import load_wiki, load_news
from src.algorithm import filter_data, join_data
from src.s3 import upload

from config.flaskconfig import SQLALCHEMY_DATABASE_URI

logging.config.fileConfig("config/logging/local.conf",
                          disable_existing_loggers=False)
logger = logging.getLogger(__name__)

logging.getLogger("s3fs").setLevel(logging.WARNING)

with open('config/config.yaml', "r") as f:
    c = yaml.load(f, Loader=yaml.FullLoader)
logger.info("Configuration file loaded from %s" % 'config/config.yaml')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Create and/or add data to database")
    parser.add_argument('step',
                        help='Which step to run',
                        choices=['load_news', 'load_wiki', 'filter',
                                 'create_db', 'join', 'ingest', 's3'])

    parser.add_argument('--input', '-i', default=None,
                        help='Path to input data')
    parser.add_argument('--input1', default=None,
                        help='Path to input data')
    parser.add_argument('--input2', default=None,
                        help='Path to input data')

    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--output', '-o', default=None,
                        help='Path to save output CSV (default = None)')

    parser.add_argument("--engine_string", default=SQLALCHEMY_DATABASE_URI,
                        help="connection URI for database")
    parser.add_argument("--s3_path",
                        help="s3 path")

    args = parser.parse_args()

    if args.step == 'load_news':
        output = load_news(args)

    elif args.step == 'load_wiki':
        output = load_wiki(args)

    elif args.step == 'create_db':
        create_db(args.engine_string)

    elif args.step == 'join':
        if args.s3_path is not None:
            logger.info('Using s3 path')
            args.input1 = args.s3_path + '/' + args.input1
            args.input2 = args.s3_path + '/' + args.input2

        output = join_data(args.input1,
                           args.input2)

    elif args.step == 'filter':
        if args.s3_path is not None:
            logger.info('Using s3 path for filtering')
            args.input = args.s3_path + '/' + args.input

        output = filter_data(args)

    elif args.step == 'ingest':
        if args.s3_path is not None:
            logger.info('Using s3 path for ingesting')
            args.input = args.s3_path + '/' + args.input

        ingest(file_path=args.input,
               engine_string=args.engine_string)

    elif args.step == 's3':
        if args.input is not None:
            upload(args.input, args.s3_path)
        if args.input1 is not None:
            upload(args.input1, args.s3_path)
        if args.input2 is not None:
            upload(args.input2, args.s3_path)

    if args.output is not None:
        output.to_csv(args.output, index=False)
        logger.info("Output saved to %s" % args.output)

        if args.s3_path is not None:
            upload(args.output, args.s3_path)
