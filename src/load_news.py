"""Module load and process news API data

Orchestration function:
    load_news(news_top_conf, source_words)

Helper functions for cleaning data:
    create_id_col(data, id_col)
    remove_stopwords(text, stopwords)

Helper function for making API calls:
    news_top(conf, timeout)
"""

import logging
import logging.config
import os
import urllib3

import requests
import pandas as pd

logging.config.fileConfig("config/logging/local.conf",
                          disable_existing_loggers=False)
logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def load_news(news_top_conf, source_words=[]):
    """Orchestration function which loads daily headlines from News API

    Args:
        news_top_conf (dict): configuration for news_top()
        source_words (list, optional): publication-related words to remove. Defaults to []

    Returns:
        (obj `pandas.DataFrame`)
    """

    logger.info('loading news from API')

    data = news_top(news_top_conf)

    all_headlines = []
    all_news = []
    all_imgs = []
    all_urls = []

    for article in data['articles']:
        all_headlines.append(article['title'])
        all_imgs.append(article['urlToImage'])
        all_urls.append(article['url'])

        # parse news headline and description
        news = article['title']
        if article['description'] is not None:
            news += ' ' + article['description']

        # remove words pertaining to publications
        source_words.append(article['source']['name'])
        news = remove_stopwords(news, source_words)
        all_news.append(news)

    news_table = pd.DataFrame({'headline': all_headlines,
                               'news': all_news,
                               'news_image': all_imgs,
                               'news_url': all_urls})
    news_table = create_id_col(news_table, 'news_id')
    return news_table


def create_id_col(data, id_col):
    """Creates enumerated id column by resetting index"""

    if id_col in data.columns:
        logger.error("'%s' already in columns; won't override", id_col)
        return data

    data.reset_index(inplace=True)
    data.rename(columns={'index': id_col}, inplace=True)
    return data


def remove_stopwords(text, stopwords):
    """remove publication words"""

    for word in stopwords:
        text = text.replace(word, '')
    return text



def news_top(conf, timeout=300):
    """ Returns `JSON` data with daily news headlines for the US

    Args:
        conf (dict): configuration containing:
            'url': url for `session.get()`
            'params': params for `session.get()` containing:
                country (str): country abbreviation (us)
                pagesize (int): controls number of headlines to consider; 100 is max
                see https://newsapi.org/docs for more params
        timeout (int): how long to wait for response before timing out; default 300 seconds

    Returns:
        object: `JSON` formatted data
    """

    NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
    if (NEWS_API_KEY is None) or (NEWS_API_KEY == ''):
        logger.error("'NEWS_API_KEY' must be sourced in environment")
        raise Exception('No API key')

    session = requests.Session()
    url = conf['url']
    params = conf['params']
    params['apiKey'] = NEWS_API_KEY

    try:
        resp = session.get(url=url, params=params, timeout=timeout)

        if resp.json()['status'] == 'error':
            logger.error("API error: %s", resp.json()['message'])
            raise Exception("API error")
        else:
            return resp.json()

    except requests.ConnectionError as exc:
        logger.error("Make sure you are connected to Internet.")
        return None

    except urllib3.exceptions.ReadTimeoutError:
        logger.warning("Timeout Error after %i seconds", timeout)
        return None

    except requests.exceptions.ReadTimeout:
        logger.warning("Timeout Error after %i seconds", timeout)
        return None

    except requests.RequestException as exc:
        logger.error("General Error: %s", str(exc))
        return None