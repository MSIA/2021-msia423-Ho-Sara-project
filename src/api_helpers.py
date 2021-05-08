import requests
import os
import logging
import logging.config

logging.config.fileConfig("config/logging/local.conf",
                          disable_existing_loggers=False)
logger = logging.getLogger(__name__)

NEWS_API_KEY = os.environ.get('NEWS_API_KEY')


def wiki_query(query):
    """ Search Wikipedia for relevant articles
    Args:
        query: `str` search query

    Returns:
        `JSON` data with wikipedia article search results
    """
    S = requests.Session()
    URL = "https://en.wikipedia.org/w/api.php"

    PARAMS = {'action': 'query',
              'format': 'json',
              'list': 'search',
              'srsearch': query}

    R = S.get(url=URL, params=PARAMS)
    return R.json()


def wiki_pagecontent(title):
    """ Obtain content from a Wikipedia page
    Args:
        title: `str` with title of Wikipedia article

    Returns:
        `JSON` data with content from the article
    """
    S = requests.Session()
    URL = "https://en.wikipedia.org/w/api.php"

    PARAMS = {'action': 'query',
              'format': 'json',
              'continue': '',
              'titles': title,
              'prop': 'extracts|pageimages',
              'exsentences': 10,
              'explaintext': 1,
              'pithumbsize': 100}

    R = S.get(url=URL, params=PARAMS)
    return R.json()


def wiki_pageinfo(title):
    """ Obtain metadata about a Wikipedia page
    Args:
        title: `str` with title

    Returns:
        `JSON` data with info about the article
    """
    S = requests.Session()
    URL = "https://en.wikipedia.org/w/api.php"

    PARAMS = {'action': 'query',
              'format': 'json',
              'continue': '',
              'titles': title,
              'prop': 'info|categories',
              'inprop': 'url'}

    R = S.get(url=URL, params=PARAMS)
    return R.json()


def news_top():
    """
    Returns:
        `JSON` data with daily news headlines for the US
    """
    if NEWS_API_KEY == '' or NEWS_API_KEY is None:
        raise Exception("Make sure NEWS_API_KEY is in environment")

    S = requests.Session()
    URL = "https://newsapi.org/v2/top-headlines?"
    PARAMS = {'apiKey': NEWS_API_KEY,
              'country': 'us',
              'pagesize': 100}
    S.get(url=URL, params=PARAMS)

    R = S.get(url=URL, params=PARAMS)
    return R.json()
