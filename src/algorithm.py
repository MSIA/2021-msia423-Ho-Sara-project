import os
from datetime import date
import yaml
import logging

from difflib import SequenceMatcher
import pandas as pd
import nltk

from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

logging.getLogger("utils").setLevel(logging.ERROR)


def sim_score(x):
    """Calculate the SequenceMatcher similarity score

    Args:
        x (array-like): containing two strings to compare

    Returns:
        (float): similarity score
    """
    return SequenceMatcher(None, x[0], x[1]).ratio()


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
    with open(args.config, 'r') as f:
        c = yaml.load(f, Loader=yaml.FullLoader)
        logger.debug("loaded yaml from : %s", args.config)

    df = pd.read_csv(args.input)
    logger.debug('read %i lines of data', len(df))

    df = remove_stopwords(df, c)
    logger.info('removed stop words')

    df['sm_sim'] = df[c['processed_features']].apply(sim_score, axis=1)
    logger.info("mean similarity score: %f", df['sm_sim'].mean())

    df['predict'] = df['sm_sim'] > c['threshhold']
    df = df.drop_duplicates(['news_id', 'title']).loc[df['predict']]

    return df
