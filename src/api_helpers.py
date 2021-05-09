import requests
import os
import urllib3
import signal
import logging
import logging.config

logging.config.fileConfig("config/logging/local.conf",
                          disable_existing_loggers=False)
logger = logging.getLogger(__name__)


def wiki_query(query, timeout=300):
    """ Given a search query, returns suggested Wikipedia pages

    Args:
        query: `str` word or phrase to search for
        timeout: `int` timeout after default 300 seconds

    Returns:
        object: `JSON` formatted data
    """
    S = requests.Session()
    URL = "https://en.wikipedia.org/w/api.php"

    PARAMS = {'action': 'query',
              'format': 'json',
              'list': 'search',
              'srsearch': query}

    try:
        R = S.get(url=URL, params=PARAMS, timeout=timeout)
        return R.json()

    except requests.ConnectionError as e:
        logger.error("Connection Error. Make sure you are connected to Internet.")
        raise Exception()

    except urllib3.exceptions.ReadTimeoutError as e:
        logger.warning("Timeout Error after %i seconds", timeout)
    except requests.exceptions.ReadTimeout as e:
        logger.warning("Timeout Error after %i seconds", timeout)
    except timeout as e:
        logger.warning("Timeout Error after %i seconds", timeout)

    except requests.RequestException as e:
        logger.error("General Error: %s", str(e))
        raise Exception()


def wiki_pagecontent(title, timeout=300):
    """ Returns `JSON` content from a given Wikipedia page

    Args:
        title: `str` title of Wikipedia article
        timeout: `int` timeout after default 300 seconds

    Returns:
        object: `JSON` formatted data
    """

    S = requests.Session()
    URL = "https://en.wikipedia.org/w/api.php"

    PARAMS = {'action': 'query',
              'format': 'json',
              'continue': '',
              'titles': title,
              'prop': 'extracts|pageimages|info|categories',
              'inprop': 'url',
              'exsentences': 10,
              'explaintext': 1,
              'pithumbsize': 100}

    signal.signal(signal.SIGALRM,
                  lambda signum, frame: 
                      logger.warning("Wiki API wait time over %i, consider trying another time", timeout))
    signal.alarm(timeout)    # Enable the alarm

    try:
        R = S.get(url=URL, params=PARAMS)
        signal.alarm(0)      # Disable the alarm
        return list(R.json()['query']['pages'].values())[0]

    except requests.ConnectionError as e:
        logger.error("Connection Error. Make sure you are connected to Internet.")
        raise Exception(e)
    except requests.RequestException as e:
        logger.error("General Error: %s", str(e))
        raise Exception(e)


def news_top(NEWS_API_KEY, country='us', pagesize=100, timeout=300):
    """ Returns `JSON` data with daily news headlines for the US

    Args:
        NEWS_API_KEY: `str` required API key from https://newsapi.org/
        country: `str` country abbreviation, defaults to US
        pagesize: `int` controls number of headlines to consider; 100 is max
        timeout: `int` timeout after default 300 seconds

    Returns:
        object: `JSON` formatted data
    """

    if NEWS_API_KEY == '':
        logger.error("Make sure NEWS_API_KEY is sourced in environment")
        raise Exception("API error")

    S = requests.Session()
    URL = "https://newsapi.org/v2/top-headlines?"
    PARAMS = {'apiKey': NEWS_API_KEY,
              'country': country,
              'pagesize': pagesize}

    try:
        R = S.get(url=URL, params=PARAMS, timeout=timeout)

        if R.json()['status'] == 'error':
            logger.error("API error: %s", R.json()['message'])
            raise Exception("API error")
        else:
            return R.json()

    except requests.ConnectionError as e:
        logger.error("Connection Error. Make sure you are connected to Internet.")
        raise Exception()

    except urllib3.exceptions.ReadTimeoutError as e:
        logger.warning("Timeout Error after %i seconds", timeout)
    except requests.exceptions.ReadTimeout as e:
        logger.warning("Timeout Error after %i seconds", timeout)
    except timeout as e:
        logger.warning("Timeout Error after %i seconds", timeout)

    except requests.RequestException as e:
        logger.error("General Error: %s", str(e))
        raise Exception()
