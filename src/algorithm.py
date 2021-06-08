""" Module containing functions to format the data for the algorithm and run it

join_data(news_path, wiki_path)
filter_data(data, conf)

helper functions:
    text_to_vector(text)
    get_cosine(x)
    remove_stopwords(data, args)

"""

from datetime import date
import logging
import math
import re
from collections import Counter

import pandas as pd

from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

logging.getLogger("utils").setLevel(logging.ERROR)


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


def filter_data(data, conf):
    """Orchestration function; clean and filter based on similarity score

    Args:
        data (obj `pandas.DataFrame`): output from join_data()
        conf (dict): yaml-style config with keys:
            'processed_features': to be processed and used for similarity score
            'threshhold': similarity score cutoff to determine relevancy

    Returns:
        (obj `pandas.DataFrame`): data with irrelevant entities removed
    """

    data = remove_stopwords(data, conf)
    logger.info('removed stop words')

    data['sim'] = data[conf['processed_features']].apply(get_cosine, axis=1)
    logger.info("mean similarity score: %f", data['sm_sim'].mean())

    data['predict'] = data['sim'] > conf['threshhold']
    data = data.drop_duplicates(['news_id', 'title']).loc[data['predict']]

    return data


def text_to_vector(text):
    """embed text based on counter"""

    word = re.compile(r"\w+")
    words = word.findall(text)
    return Counter(words)


def get_cosine(x):
    """calculate cosine of text-embedded vectors"""

    vec1 = text_to_vector(x[0])
    vec2 = text_to_vector(x[1])

    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in list(vec1.keys())])
    sum2 = sum([vec2[x] ** 2 for x in list(vec2.keys())])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    return float(numerator) / denominator


def remove_stopwords(data, args):
    """remove stopwords from specified dataframe columns

    Args:
        data (obj `pandas.DataFrame`): dataframe with some str columns
        args (dict): yaml-style config with keys
            'raw_features' and 'processed_features'

    Returns:
        (obj `pandas.DataFrame`): dataframe, but with a processed str
                                  column with stopwords removed
    """
    stop_words = stopwords.words('english')

    for raw, proc in zip(args['raw_features'], args['processed_features']):
        data[proc] = data[raw].str.lower().str.split(). \
            apply(lambda x: ' '.join([item for item in x
                                      if item not in stop_words]))

    logger.debug("removed stopwords, returning processed data")
    return data
