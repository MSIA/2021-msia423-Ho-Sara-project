import os
import argparse
import logging
import logging.config
import yaml

import pandas as pd

from src.load import load_wiki, load_news
from src.algorithm import filter_data, join_data
from src.db import create_db
from src.ingest import IngestManager

from config.flaskconfig import SQLALCHEMY_DATABASE_URI

NEWS_API_KEY = os.environ.get('NEWS_API_KEY')

logging.config.fileConfig("config/logging/local.conf",
                          disable_existing_loggers=False)
logger = logging.getLogger(__name__)

with open('config/config.yaml', "r") as f:
    c = yaml.load(f, Loader=yaml.FullLoader)
print(c)
logger.info("Configuration file loaded from %s" % 'config/config.yaml')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Create and/or add data to database")
    parser.add_argument('step',
                        help='Which step to run',
                        choices=['load_news', 'load_wiki', 'filter',
                                 'create_db', 'join', 'ingest'])

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

    args = parser.parse_args()

    if args.input is not None:
        input = pd.read_csv(args.input)
        logger.info('Input data loaded from %s', args.input)

    if args.step == 'load_news':
        output = load_news(NEWS_API_KEY)

    elif args.step == 'load_wiki':
        output = load_wiki(args.input,
                           n_results=c['n_results'])

    elif args.step == 'create_db':
        create_db(args.engine_string)

    elif args.step == 'join':
        output = join_data(args.input1,
                           args.input2)

    elif args.step == 'ingest':
        ing = IngestManager(file_path=args.input,
                            engine_string=args.engine_string)
        ing.ingest()

    # else:
    #     test.run_tests(args)

    if args.output is not None:
        output.to_csv(args.output, index=False)
        logger.info("Output saved to %s" % args.output)
