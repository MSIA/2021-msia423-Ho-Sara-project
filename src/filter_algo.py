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
        x (array-like): containing two strings to compares

    Returns:
        float: similarity score
    """
    return SequenceMatcher(None, x[0], x[1]).ratio()


def remove_stopwords(df):
    stop_words = stopwords.words('english')
    stop_words.extend(['from', 'subject', 're', 'edu', 'use'])

    df['wiki_process'] = df['wiki'].str.lower().str.split().apply(lambda x: ' '.join([item for item in x if item not in stop_words]))
    df['news_process'] = df['news'].str.lower().str.split().apply(lambda x: ' '.join([item for item in x if item not in stop_words]))
    return df


def join_data(datadir):

    wikidf = []
    newsdf = []

    for file in os.listdir(datadir):
        if 'wiki' in file:
            df = pd.read_csv(datadir + '/' + file)

            # remove duplicates
            df.drop_duplicates(['title', 'news_id'])

            # create index / primary key
            df = df.reset_index()
            df.rename(columns={'index': 'wiki_id'}, inplace=True)
            wikidf.append(df)

        elif 'news' in file:
            df = pd.read_csv(datadir + '/' + file)
            newsdf.append(df)

    joined = pd.concat(wikidf).merge(pd.concat(newsdf), on=['news_id'])
    joined['date'] = date.today().strftime("%b-%d-%Y")
    joined = joined.sort_values(['news_id', 'wiki_id'])
    return joined


def filter_data(datadir):

    df = join_data(datadir)

    df = df.dropna()
    df = remove_stopwords(df)

    df['sm_sim'] = df[['wiki_process', 'news_process']].apply(sim_sm, axis=1)
    df['predict'] = df['sm_sim'] > 0.2
    df.drop_duplicates(['news_id', 'title']).loc[df['predict']]

    return df
