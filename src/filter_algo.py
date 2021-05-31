import os

import nltk
from difflib import SequenceMatcher
from nltk.corpus import stopwords
import pandas as pd


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

    df['wiki'] = df['wiki'].str.lower().str.split()
    df['news'] = df['news'].str.lower().str.split()
    df['wiki'] = df['wiki'].apply(lambda x: ' '.join([item for item in x if item not in stop_words]))
    df['news'] = df['news'].apply(lambda x: ' '.join([item for item in x if item not in stop_words]))
    return df


def join_data(datadir):

    wikidf = []
    newsdf = []

    for file in os.listdir(datadir):
        if 'wiki' in file:
            df = pd.read_csv(datadir + '/' + file)

            # add date column
            date = '-'.join(file.split('-')[0:3])
            df['date'] = date

            # remove duplicates
            df.drop_duplicates(['title', 'news_id', 'date'])

            # set index
            df = df.reset_index()
            df.rename(columns={'index': 'wiki_id'}, inplace=True)
            wikidf.append(df)

        elif 'news' in file:
            df = pd.read_csv(datadir + '/' + file)
            date = '-'.join(file.split('-')[0:3])
            df['date'] = date
            newsdf.append(df)

    data = pd.concat(wikidf).merge(pd.concat(newsdf), on=['news_id', 'date'])
    print(data.columns)
    data = data.sort_values(['date', 'news_id', 'wiki_id'])
    return data


def filter_data(df):
    df = df.dropna()
    df = remove_stopwords(df)

    df['sm_sim'] = df[['wiki', 'news']].apply(sim_sm, axis=1)
    df['predict'] = df['sm_sim'] > 0.2
    df.drop_duplicates(['news_id', 'title']).loc[df['predict']]

    return df


if __name__ == '__main__':

    df = join_data('./data/sample')
    filter_data(df).to_csv('./data/sample/May-29-2021-joined.csv', index=False)
