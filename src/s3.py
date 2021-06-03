import os
import logging

import boto3
import botocore

logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s', level=logging.DEBUG)
logging.getLogger("botocore").setLevel(logging.ERROR)
logging.getLogger("s3transfer").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("boto3").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("aiobotocore").setLevel(logging.ERROR)
logging.getLogger("s3fs").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


def upload(local_path, s3path):
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
            logger.error('Please provide credentials via AWS_ACCESS_KEY_ID ',
                         'and AWS_SECRET_ACCESS_KEY env variables')
        else:
            logger.info('Data uploaded to %s', {s3path} + '/raw/' + {file})


def s3_static():
    upload('data/labeled', s3path)
    upload('data/sample', s3path)


def s3_dynamic():
    upload(, s3path)
