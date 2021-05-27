from datetime import date
import logging
import logging.config
import signal

import spacy
import pandas as pd

from src.api_helpers import wiki_query, wiki_pagecontent, news_top

logging.config.fileConfig("config/logging/local.conf",
                          disable_existing_loggers=False)
logger = logging.getLogger(__name__)


def load_news(NEWS_API_KEY, directory='./data'):
    """Create pandas dataframe from daily headlines from News API

    Args:
        NEWS_API_KEY: `str` generated from https://newsapi.org/
        directory: local directory to save .csv file

    Returns:
        obj `pandas.DataFrame`
    """
    today = date.today().strftime("%b-%d-%Y")
    logger.info('loading news from API')

    try:
        data = news_top(NEWS_API_KEY)
    except Exception as e:
        logger.error(f'Error {e} when retrieving headlines')

    news = []
    content = []
    img = []
    url = []
    for article in data['articles']:

        headline = article['title']
        if article['description'] is not None:
            headline += article['description']

        # remove publication information
        headline = headline.replace(article['source']['name'], ' ')
        news.append(headline)
        content.append(article['content'])
        img.append(article['urlToImage'])
        url.append(article['url'])

    news_table = pd.DataFrame({'news': news,
                               'content': content,
                               'img': img,
                               'url': url}).reset_index()
    news_table.columns = ['news_id', 'news', 'content', 'img', 'url']

    try:
        news_table.to_csv(f'{directory}/{today}-news-entries.csv', index=False)
        logger.info("----Saved %i headlines to csv", len(news_table))
    except FileNotFoundError as e:
        logger.warning('----Error in saving csv locally; Still returning DataFrame obj')
        logger.warning(e)

    return news_table


def news2entities(news):
    """ Use space to convert a news description into lists of entities and labels """

    nlp = spacy.load("en_core_web_sm")
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

    return entities, labels


def load_wiki(news_table, directory='./data', n_results=3, timeout=300):
    """Match news with wikipedia articles

    Args:
        news_table: pandas dataframe with news headlines
        timeout: `int` number of seconds to wait for a wiki API query

    Returns: obj `pandas.DataFrame`

    """

    today = date.today().strftime("%b-%d-%Y")
    nlp = spacy.load("en_core_web_sm")
    logger.info('matching news with wiki entries from Wikipedia API')

    table_data = []
    for _, row in news_table.iterrows():
        news_id, news, content, _, _ = row

        logger.info("----Processing '%s...'", news[0:25])

        entities, labels = news2entities(news)
        for ent, label in zip(entities, labels):
            articledata = wiki_query(ent)
            search_results = articledata['query']['search']

            for result in search_results[0:n_results]:  # take the top 3
                title = result['title']

                info = wiki_pagecontent(title)
                try:
                    categories = info['categories']
                    categories = [kv['title'] for kv in categories if 'births' not in kv['title']]
                except KeyError:
                    pass

                if 'Category:Disambiguation pages' in categories:
                    pass
                else:

                    if 'thumbnail' in info:
                        image = info['thumbnail']['source']
                    else:
                        image = ''

                    table_data.append({'news_id': news_id,
                                       'entity': ent,
                                       'label': label,
                                       'title': info['title'],
                                       'category': categories[0],
                                       'revised': info['touched'],
                                       'url': info['fullurl'],
                                       'wiki': info['extract'],
                                       'image': image})

    table = pd.DataFrame(table_data)
    try:
        table.to_csv(f'{directory}/{today}-wiki-entries.csv', index=False)
        logger.info("----Saved %i wiki entries to csv", len(table))
    except FileNotFoundError as e:
        logger.warning('----Error in saving csv locally; still returning DataFrame obj')
        logger.warning(e)

    return table
