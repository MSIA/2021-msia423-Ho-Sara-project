from datetime import date
import logging
import logging.config

import spacy
import pandas as pd

from src.api_helpers import *

logging.config.fileConfig("config/logging/local.conf",
                          disable_existing_loggers=False)
logger = logging.getLogger(__name__)


def load_news():
    """Create pandas dataframe from daily headlines from News API
    Args:
        None

    Returns: obj `pandas.DataFrame`

    """
    logger.info('loading news from API')
    data = news_top()
    news = []
    for article in data['articles']:

        headline = article['title']
        if article['description'] is not None:
            headline += article['description']

        # remove publication information
        headline = headline.replace(article['source']['name'], '')
        news.append(headline)

    news_table = pd.DataFrame(news).reset_index()
    news_table.columns = ['news_id', 'news']

    today = date.today().strftime("%b-%d-%Y")
    news_table.to_csv(f'./data/{today}-news-entries', index=False)
    logger.info(f"----Saved to csv data for {len(news_table)} headlines...")
    return news_table


def load_wiki(news_table):
    """Match news with wikipedia articles
    Args:
        pandas dataframe with news headlines

    Returns: obj `pandas.DataFrame`

    """
    nlp = spacy.load("en_core_web_sm")

    logger.info('matching news with wiki entries from Wikipedia API')
    table_data = []
    for _, row in news_table.iterrows():
        news_id, news = row

        logger.info(f"----Processing '{news[0:25]}...'")

        # start to break query into named entities
        doc = nlp(news)

        entities = []
        labels = []
        for ent in doc.ents:
            if (ent.label_ in ['PERSON', 'FAC', 'ORG', 'NORP', 'PRODUCT']) and (ent.text not in entities):
                if ent.label_ == 'PERSON':
                    labels.append('PERSON')
                elif ent.label_ == 'NORP':
                    labels.append('GROUP')
                elif ent.label_ == 'ORG':
                    labels.append('ORGANIZATION')
                else:
                    labels.append('')

                entities.append(ent.text)

        for ent, label in zip(entities, labels):
            articledata = wiki_query(ent)

            try:
                search_results = articledata['query']['search']

                for result in search_results[0:3]:  # take the top 3
                    title = result['title']
                    info = wiki_pageinfo(title)
                    info = list(info['query']['pages'].values())[0]

                    categories = [kv['title'] for kv in info['categories'] if 'births' not in kv['title']]

                    # ignore diambiguation pages
                    if 'Category:Disambiguation pages' in categories:
                        pass
                    else:
                        content = list(wiki_pagecontent(title)['query']['pages'].values())[0]
                        if 'thumbnail' in content:
                            image = content['thumbnail']['source']
                        else:
                            image = ''
                        table_data.append({'news_id': news_id,
                                           'entity': ent,
                                           'label': label,
                                           'title': info['title'],
                                           'category': categories[0],
                                           'revised': info['touched'],
                                           'url': info['fullurl'],
                                           'wiki': content['extract'],
                                           'image': image})

            except(IndexError):
                continue

    table = pd.DataFrame(table_data)
    today = date.today().strftime("%b-%d-%Y")
    table.to_csv(f'./data/{today}-wiki-entries.csv',
                 index=False)
    return table
