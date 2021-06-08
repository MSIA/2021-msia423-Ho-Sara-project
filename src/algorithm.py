""" Module containing functions to format the data for the algorithm and run it

"""

from datetime import date
from difflib import SequenceMatcher
import logging
import math
import re
from collections import Counter

import yaml
import pandas as pd
from scipy import stats

from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

logging.getLogger("utils").setLevel(logging.ERROR)


def text_to_vector(text):
    word = re.compile(r"\w+")
    words = word.findall(text)
    return Counter(words)


def get_cosine(x):
    vec1 = text_to_vector(x[0])
    vec2 = text_to_vector(x[1])

    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in list(vec1.keys())])
    sum2 = sum([vec2[x] ** 2 for x in list(vec2.keys())])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator


def remove_stopwords(df, args):
    """remove stopwords from specified dataframe columns

    Args:
        df (obj `pandas.DataFrame`): dataframe with some str columns
        args (dict): yaml-style config with keys
            'raw_features' and 'processed_features'

    Returns:
        (obj `pandas.DataFrame`): dataframe, but with a processed str
                                  column with stopwords removed
    """
    stop_words = stopwords.words('english')

    for raw, proc in zip(args['raw_features'], args['processed_features']):
        df[proc] = df[raw].str.lower().str.split(). \
            apply(lambda x: ' '.join([item for item in x
                                      if item not in stop_words]))

    logger.debug("removed stopwords, returning processed df")
    return df


def join_data(news_path, wiki_path):
    """Join news file with wiki file

    Args:
        news_path (str): file path
        wiki_path (str): file path

    Returns:
        (obj `pandas.DataFrame`): joined dataframe
    """

    wikidf = pd.read_csv(wiki_path)
    wikidf.drop_duplicates(['title', 'news_id'])
    wikidf.reset_index(inplace=True)
    wikidf.rename(columns={'index': 'wiki_id'}, inplace=True)

    newsdf = pd.read_csv(news_path)

    joined = wikidf.merge(newsdf, on=['news_id'])
    joined['date'] = date.today().strftime("%b-%d-%Y")
    return joined


def filter_data(args):
    """Orchestration function; clean and filter based on similarity score

    Args:
        args (dict): yaml-style config with keys:
            'config': yaml file path
            'input': file path of joined() ouput
            'processed_features': to be processed and used for similarity score
            'threshhold': similarity score cutoff to determine relevancy

    Returns:
        (obj `pandas.DataFrame`): data with irrelevant entities removed
    """
    with open(args.config, 'r') as conf_file:
        conf = yaml.load(conf_file, Loader=yaml.FullLoader)
        logger.debug("loaded yaml from : %s", args.config)

    df = pd.read_csv(args.input)
    logger.debug('read %i lines of data', len(df))

    df = remove_stopwords(df, conf)
    logger.info('removed stop words')

    df['sm_sim'] = df[conf['processed_features']].apply(cos_pipeline, axis=1)
    logger.info("mean similarity score: %f", df['sm_sim'].mean())

    df['predict'] = df['sm_sim'] > conf['threshhold']
    df = df.drop_duplicates(['news_id', 'title']).loc[df['predict']]

    return df


def eval_(args):
    args.input()

