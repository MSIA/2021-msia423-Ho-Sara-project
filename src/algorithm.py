import os
from datetime import date

from difflib import SequenceMatcher
import pandas as pd
import nltk

nltk.download('stopwords')
from nltk.corpus import stopwords


def sim_sm(x):
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
        df (pandas dataframe): dataframe with some str columns
        args (dict): dict with 'config': yaml file path

    Returns:
        (pandas dataframe): dataframe, but with processed str
                               columns with stopwords removed
    """
    stop_words = stopwords.words('english')

    with open(args.config, 'r') as f:
        c = yaml.load(f, Loader=yaml.FullLoader)

    for raw, processed in zip(c['raw_features'], c['processed_features']):
        df[processed] = df[raw].str.lower().str.split(). \
            apply(lambda x: ' '.join([item for item in x
                                      if item not in stop_words]))

    return df


def join_data(news_path, wiki_path):
    """Join news file with wiki file

    Args:
        news_path (str): file path
        wiki_path (str): file path

    Returns:
        (pandas dataframe): joined dataframe
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
    """Filter data based on arguments

    Args:
        args (dict): dict with 'config': yaml file path
                     and 'input': file path of joined() ouput

    Returns:
        (pandas dataframe): data with irrelevant entities removed
    """
    with open(args.config, 'r') as f:
        c = yaml.load(f, Loader=yaml.FullLoader)

    df = pd.read_csv(args.input)

    df = df.dropna()
    df = remove_stopwords(df)

    df['sm_sim'] = df[c['processed_features']].apply(sim_sm, axis=1)
    df['predict'] = df['sm_sim'] > c['threshhold']
    df.drop_duplicates(['news_id', 'title']).loc[df['predict']]

    return df
