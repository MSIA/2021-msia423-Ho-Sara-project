import os
import argparse
import logging
import logging.config
import yaml

import pandas as pd
import boto3
import botocore
import spacy

from src.load import load_wiki, load_news
from src.ingest import *
from src.algorithm import filter_data, join_data

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


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Create and/or add data to database")
    parser.add_argument('step', 
                        help='Which step to run', 
                        choices=['load_news', 'load_wiki', 'filter', 'create_db', 'join', 'ingest'])

    parser.add_argument('--input', '-i', default=None, 
                        help='Path to input data')
    parser.add_argument('--input1', default=None, 
                        help='Path to input data')
    parser.add_argument('--input2', default=None, 
                        help='Path to input data')

    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--output', '-o', default=None,
                        help='Path to save output CSV (optional, default = None)')
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
        output = load_wiki(args.input, n_results=1)

    elif args.step == 'create_db':
        create_db(args.engine_string)

    elif args.step == 'join':
        output = join_data(args.input1, args.input2)

    elif args.step == 'ingest':
        ingest(args.input, args.engine_string)

    # else:
    #     test.run_tests(args)

    if args.output is not None:
        output.to_csv(args.output, index=False)
        logger.info("Output saved to %s" % args.output)
