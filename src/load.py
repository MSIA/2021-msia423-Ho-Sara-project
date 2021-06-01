from datetime import date
import logging
import logging.config
import requests
import os
import urllib3
import signal

import spacy
import pandas as pd


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
            headline += ' ' + article['description']

        # remove publication information
        headline = headline.replace(article['source']['name'], ' ')
        source_words = ['USA TODAY', 'POLITICO', 'TheHill']

        news.append(headline)
        content.append(article['content'])
        img.append(article['urlToImage'])
        url.append(article['url'])

    news_table = pd.DataFrame({'news': news,
                               'news_image': img,
                               'news_url': url}).reset_index()
    news_table.columns = ['news_id', 'news', 'news_image', 'news_url']

    return news_table


def news2entities(news):
    """ Use space to convert a news description into lists of entities and labels """

    nlp = spacy.load("en_core_web_sm")
    doc = nlp(news)

    entities = []
    for ent in doc.ents:
        if (ent.label_ in ['PERSON', 'FAC', 'ORG', 'NORP', 'PRODUCT']) and (ent.text not in entities):
            text = ent.text
            if ent.label_ == 'ORG':
                text += ' (organization)'
            entities.append(text)

    return entities


def load_wiki(input_file, directory='./data', n_results=3, timeout=300):
    """Match news with wikipedia articles

    Args:
        news_table: pandas dataframe with news headlines
        timeout: `int` number of seconds to wait for a wiki API query

    Returns: obj `pandas.DataFrame`

    """

    logger.info('matching news with wiki entries from Wikipedia API')
    today = date.today().strftime("%b-%d-%Y")
    nlp = spacy.load("en_core_web_sm")

    news_table = pd.read_csv(input_file)

    table_data = []
    for _, row in news_table.iterrows():
        news_id, news, _, _ = row

        logger.info("----Processing '%s...'", news[0:25])

        entities = news2entities(news)
        titles = []
        for ent in entities:
            articledata = wiki_query(ent)
            search_results = articledata['query']['search']

            # n_results is how many search results to consider matching
            for result in search_results[0:n_results]:
                title = result['title']
                if title in titles:
                    pass

                info = wiki_pagecontent(title)
                try:
                    categories = info['categories']
                    categories = [kv['title'] for kv in categories if 'births' not in kv['title']]
                    if 'Category:Disambiguation pages' in categories:
                        pass
                except KeyError:
                    pass

                if 'thumbnail' in info:
                    image = info['thumbnail']['source']
                else:
                    image = ''

                table_data.append({'news_id': news_id,
                                   'entity': ent,
                                   'title': info['title'],
                                   'wiki': info['extract'],
                                   'wiki_url': info['fullurl'],
                                   'wiki_image': image})
                titles.append(title)

    table = pd.DataFrame(table_data)

    return table


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
