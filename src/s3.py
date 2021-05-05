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


def parse_s3(s3path):
    regex = r"s3://([\w._-]+)/([\w./_-]+)"

    m = re.match(regex, s3path)
    s3bucket = m.group(1)
    s3path = m.group(2)

    return s3bucket, s3path


def upload_files_to_s3(local_path, s3path):

    s3bucket, s3_just_path = parse_s3(s3path)

    s3 = boto3.resource("s3")
    bucket = s3.Bucket(s3bucket)

    try:
        bucket.upload_file(local_path, s3_just_path)
    except botocore.exceptions.NoCredentialsError:
        logger.error('Please provide AWS credentials via AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env variables.')
    else:
        logger.info(f'Data uploaded from {local_path} to {s3path}')


def upload_to_s3_pandas(local_path, s3path, sep=';'):

    files = os.listdir('./data')
    for file in files:
        df = pd.read_csv(local_path + file, sep=sep)

        try:
            df.to_csv(s3path + file, sep=sep)
        except botocore.exceptions.NoCredentialsError:
            logger.error('Please provide AWS credentials via AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env variables.')
        else:
            logger.info(f'Data uploaded from {local_path} to {s3path}')


# def download_files_from_s3(local_path, s3path):

#     s3bucket, s3_just_path = parse_s3(s3path)

#     s3 = boto3.resource("s3")
#     bucket = s3.Bucket(s3bucket)

#     try:
#         bucket.download_file(s3_just_path, local_path)
#     except botocore.exceptions.NoCredentialsError:
#         logger.error('Please provide AWS credentials via AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env variables.')
#     else:
#         logger.info('Data downloaded from %s to %s', s3path, local_path)


# def download_from_s3_pandas(local_path, s3path, sep=';'):

#     try:
#         df = pd.read_csv(s3path, sep=sep)
#     except botocore.exceptions.NoCredentialsError:
#         logger.error('Please provide AWS credentials via AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env variables.')
#     else:
#         df.to_csv(local_path, sep=sep)
#         logger.info('Data uploaded from %s to %s', local_path, s3path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sep',
                        default=';',
                        help="CSV separator if using pandas")
    parser.add_argument('--load', default='False',
                        help="load data?")
    parser.add_argument('--pandas', default=False, action='store_true',
                        help="If used, will load data via pandas")
    # parser.add_argument('--download', default=False, action='store_true',
    #                     help="If used, will load data via pandas")
    parser.add_argument('--s3path', default='s3://2021-msia-423-ho-sara',
                        help="If used, will load data via pandas")
    parser.add_argument('--local_path', default='./data',
                        help="Where to load data to in S3")
    args = parser.parse_args()

    # if args.download:
    #     if args.pandas:
    #         download_from_s3_pandas(args.local_path, args.s3path, args.sep)
    #     else:
    #         download_files_from_s3(args.local_path, args.s3path)
    # else:
    if args.load:
        news = load_news()
        load_wiki(news)

    if args.pandas:
        upload_to_s3_pandas(args.local_path, args.s3path, args.sep)
    else:
        upload_files_to_s3(args.local_path, args.s3path)
