from datetime import date
import logging
import logging.config
import os
import urllib3
import signal

import yaml
import requests
import pandas as pd
import spacy

logging.config.fileConfig("config/logging/local.conf",
                          disable_existing_loggers=False)
logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def load_news(args):
    """Create pandas dataframe from daily headlines from News API

    Args:
        NEWS_API_KEY: `str` generated from https://newsapi.org/
        directory: local directory to save .csv file

    Returns:
        obj `pandas.DataFrame`
    """
    with open(args.config, 'r') as f:
        c = yaml.load(f, Loader=yaml.FullLoader)

    today = date.today().strftime("%b-%d-%Y")
    logger.info('loading news from API')

    data = news_top(args)

    headline = []
    news = []
    img = []
    url = []
    for article in data['articles']:

        headline.append(article['title'])
        img.append(article['urlToImage'])
        url.append(article['url'])

        full = article['title']

        if article['description'] is not None:
            full += ' ' + article['description']

        # remove publication information
        full = full.replace(article['source']['name'], ' ')
        source_words = c['source_words']
        for word in source_words:
            full = full.replace(word, '')

        news.append(full)

    news_table = pd.DataFrame({'headline': headline,
                               'news': news,
                               'news_image': img,
                               'news_url': url}).reset_index()
    news_table.columns = ['news_id', 'headline', 'news',
                          'news_image', 'news_url']

    return news_table


def news2entities(news, c):
    """ Use space to convert a news description
    into lists of entities and labels """

    nlp = spacy.load(c['spacy_model'])
    doc = nlp(news)

    entities = []
    for ent in doc.ents:
        if (ent.label_ in c['stop_spacy']) and (ent.text not in entities):
            text = ent.text
            if ent.label_ == 'ORG':
                text += ' (organization)'
            entities.append(text)

    return entities


def load_wiki(args):
    """Match news with wikipedia articles

    Args:
        news_table: pandas dataframe with news headlines
        timeout: `int` number of seconds to wait for a wiki API query

    Returns:
        obj `pandas.DataFrame`
    """
    with open(args.config, 'r') as f:
        c = yaml.load(f, Loader=yaml.FullLoader)

    logger.info('matching news with wiki entries from Wikipedia API')
    today = date.today().strftime("%b-%d-%Y")
    nlp = spacy.load("en_core_web_sm")

    news_table = pd.read_csv(args.input)

    table_data = []
    for _, row in news_table.iterrows():
        news_id, _, news, _, _ = row

        logger.info("----Processing '%s...'", news[0:25])

        entities = news2entities(news, c)
        titles = []
        for ent in entities:
            articledata = wiki_query(ent, **c)
            search_results = articledata['query']['search']

            # n_results is how many search results to consider matching
            for result in search_results[0:c['load_wiki']['n_results']]:
                title = result['title']
                if title in titles:
                    pass

                info = wiki_pagecontent(title, **c)
                try:
                    categories = info['categories']
                    categories = ' '.join([kv['title']
                                          for kv in categories]).lower()

                    stop_categories = c['stop_categories']
                    for stop_category in stop_categories:
                        if stop_category in categories:
                            pass
                except KeyError:
                    pass

                if 'thumbnail' in info:
                    image = info['thumbnail']['source']
                else:
                    image = ''

                wiki = info['extract']
                stop_phrases = c['stop_phrases']
                for stop_phrase in stop_phrases:
                    if stop_phrase in wiki:
                        pass

                if '==' in wiki:
                    end = wiki.find('==')
                    wiki = wiki[0:end]

                logger.info("%s found as a match, info['title']")
                table_data.append({'news_id': news_id,
                                   'entity': ent,
                                   'title': info['title'],
                                   'wiki': wiki,
                                   'wiki_url': info['fullurl'],
                                   'wiki_image': image})
                titles.append(title)

    table = pd.DataFrame(table_data)

    return table


def wiki_query(query, **c):
    """ Given a search query, returns suggested Wikipedia pages

    Args:
        query: `str` word or phrase to search for
        timeout: `int` timeout after default 300 seconds

    Returns:
        object: `JSON` formatted data
    """
    S = requests.Session()
    url = c['wiki_url']
    params = c['wiki_query']
    params['srsearch'] = query

    try:
        R = S.get(url=url, params=params, timeout=c['timeout'])
        return R.json()

    except requests.ConnectionError as e:
        logger.error("Connection Error. ",
                     "Make sure you are connected to Internet.")
        raise Exception()

    except urllib3.exceptions.ReadTimeoutError as e:
        logger.warning("Timeout Error after %i seconds", c['timeout'])
    except requests.exceptions.ReadTimeout as e:
        logger.warning("Timeout Error after %i seconds", c['timeout'])

    except requests.RequestException as e:
        logger.error("General Error: %s", str(e))
        raise Exception()


def wiki_pagecontent(title, **c):
    """ Returns `JSON` content from a given Wikipedia page

    Args:
        title: `str` title of Wikipedia article
        timeout: `int` timeout after default 300 seconds

    Returns:
        object: `JSON` formatted data
    """
    logger.debug("gathering pagecontent for page %s", title)

    S = requests.Session()
    url = c['wiki_url']
    params = c['wiki_pagecontent']
    params['titles'] = title

    signal.signal(signal.SIGALRM,
                  lambda signum, frame:
                      logger.warning("Wiki API wait time over %i, ",
                                     "consider trying another time",
                                     c['timeout']))
    signal.alarm(c['timeout'])    # Enable the alarm

    try:
        R = S.get(url=url, params=params)
        signal.alarm(0)      # Disable the alarm
        return list(R.json()['query']['pages'].values())[0]

    except requests.ConnectionError as e:
        logger.error("Connection Error. ",
                     "Make sure you are connected to Internet.")
        raise Exception(e)
    except requests.RequestException as e:
        logger.error("General Error: %s", str(e))
        raise Exception(e)


def news_top(args):
    """ Returns `JSON` data with daily news headlines for the US

    Args:
        NEWS_API_KEY: `str` required API key from https://newsapi.org/
        country: `str` country abbreviation, defaults to US
        pagesize: `int` controls number of headlines to consider; 100 is max
        timeout: `int` timeout after default 300 seconds

    Returns:
        object: `JSON` formatted data
    """
    with open(args.config, 'r') as f:
        c = yaml.load(f, Loader=yaml.FullLoader)

    NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
    if (NEWS_API_KEY is None) or (NEWS_API_KEY == ''):
        raise Exception(f'No API key')

    S = requests.Session()
    url = c['news_url']
    params = c['news_top']
    params['apiKey'] = NEWS_API_KEY

    try:
        R = S.get(url=url, params=params, timeout=c['timeout'])

        if R.json()['status'] == 'error':
            logger.error("API error: %s", R.json()['message'])
            raise Exception("API error")
        else:
            return R.json()

    except requests.ConnectionError as e:
        logger.error("Connection Error. ",
                     "Make sure you are connected to Internet.")
        raise Exception()

    except urllib3.exceptions.ReadTimeoutError as e:
        logger.warning("Timeout Error after %i seconds", c['timeout'])
    except requests.exceptions.ReadTimeout as e:
        logger.warning("Timeout Error after %i seconds", c['timeout'])

    except requests.RequestException as e:
        logger.error("General Error: %s", str(e))
        raise Exception()
