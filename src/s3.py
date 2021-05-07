import argparse
import logging
import re
import os

import pandas as pd
import boto3
import botocore

from load_data import *

logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s', level=logging.DEBUG)
logging.getLogger("botocore").setLevel(logging.ERROR)
logging.getLogger("s3transfer").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("boto3").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("aiobotocore").setLevel(logging.ERROR)
logging.getLogger("s3fs").setLevel(logging.ERROR)

logger = logging.getLogger('s3')


def upload_files_to_s3(local_path, s3path):

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
            logger.info(f'Data uploaded from {local_path}/{file} to {s3path}/raw/{file}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--load', default=False,
                        help="Load new data into local folder via API")
    parser.add_argument('--s3path', default='s3://2021-msia-423-ho-sara',
                        help="If used, will load data to s3")
    parser.add_argument('--local_path', default='./data',
                        help="Where to load data to in S3")
    args = parser.parse_args()

    if args.load:
        # this will save csv files into local path with new daily data
        news = load_news()
        load_wiki(news)

    upload_files_to_s3(args.local_path, args.s3path)
