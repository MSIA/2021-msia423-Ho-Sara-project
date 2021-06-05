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


def upload(local_file, s3_path):
    """ Upload local files to s3 """

    s3bucket = s3_path.replace('s3://', '')

    s3 = boto3.resource("s3")
    bucket = s3.Bucket(s3bucket)

    try:
        bucket.upload_file(f'{local_file}', f'{local_file}')
    except botocore.exceptions.NoCredentialsError:
        logger.error('Please provide credentials via AWS_ACCESS_KEY_ID ',
                     'and AWS_SECRET_ACCESS_KEY env variables')
    else:
        logger.info('Data uploaded to s3 path %s', local_file)
