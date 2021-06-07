"""Module containing functions to load and process API data

"""

import logging
import logging.config
import os
import signal
import urllib3

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
    with open(args.config, 'r') as conf_file:
        conf = yaml.load(conf_file, Loader=yaml.FullLoader)

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
        source_words = conf['source_words']
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


def news2entities(news, conf):
    """ Use space to convert a news description
    into lists of entities and labels """

    nlp = spacy.load(conf['spacy_model'])
    doc = nlp(news)

    entities = []
    for ent in doc.ents:
        if (ent.label_ in conf['stop_spacy']) and (ent.text not in entities):
            text = ent.text
            if ent.label_ == 'ORG':
                text += ' (organization)'
            entities.append(text)

    return entities


def load_wiki(args):
    """Orchestration function which matches news with wikipedia articles

    Args:
        news_table: pandas dataframe with news headlines
        timeout: `int` number of seconds to wait for a wiki API query

    Returns:
        obj `pandas.DataFrame`
    """
    with open(args.config, 'r') as conf_file:
        conf = yaml.load(conf_file, Loader=yaml.FullLoader)

    logger.info('matching news with wiki entries from Wikipedia API')
    nlp = spacy.load("en_core_web_sm")

    news_table = pd.read_csv(args.input)

    table_data = []
    for _, row in news_table.iterrows():
        news_id, _, news, _, _ = row

        logger.info("----Processing '%s...'", news[0:25])

        entities = news2entities(news, conf)
        titles = []
        for ent in entities:
            articledata = wiki_query(ent, **conf)
            search_results = articledata['query']['search']

            # n_results is how many search results to consider matching
            for result in search_results[0:conf['load_wiki']['n_results']]:
                title = result['title']
                if title in titles:
                    logger.debug('%s has already been added', title)
                    continue

                info = wiki_pagecontent(title, **conf)
                try:
                    categories = info['categories']
                    categories = ' '.join([kv['title']
                                          for kv in categories]).lower()

                    stop_categories = conf['stop_categories']
                    for stop_category in stop_categories:
                        if stop_category in categories:
                            continue
                except KeyError:
                    continue

                if 'thumbnail' in info:
                    image = info['thumbnail']['source']
                else:
                    image = ''

                wiki = info['extract']
                stop_phrases = conf['stop_phrases']
                for stop_phrase in stop_phrases:
                    if stop_phrase in wiki:
                        continue

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


def wiki_query(query, **conf):
    """ Given a search query, returns suggested Wikipedia pages

    Args:
        query: `str` word or phrase to search for
        timeout: `int` timeout after default 300 seconds

    Returns:
        object: `JSON` formatted data
    """
    session = requests.Session()
    url = conf['wiki_url']
    params = conf['wiki_query']

    # add query to the parameters, required by API
    params['srsearch'] = query

    try:
        return session.get(url=url,
                           params=params,
                           timeout=conf['timeout']).json()

    except requests.ConnectionError:
        logger.error("Make sure you are connected to Internet.")
        return None

    except urllib3.exceptions.ReadTimeoutError:
        logger.warning("Timeout Error after %i seconds", conf['timeout'])
        return None

    except requests.exceptions.ReadTimeout:
        logger.warning("Timeout Error after %i seconds", conf['timeout'])
        return None

    except requests.RequestException as exc:
        logger.error("General Error: %s", exc)
        return None


def wiki_pagecontent(title, **conf):
    """ Returns `JSON` content from a given Wikipedia page

    Args:
        title: `str` title of Wikipedia article
        timeout: `int` timeout after default 300 seconds

    Returns:
        object: `JSON` formatted data
    """
    logger.debug("gathering pagecontent for page %s", title)

    session = requests.Session()
    url = conf['wiki_url']
    params = conf['wiki_pagecontent']
    params['titles'] = title

    signal.signal(signal.SIGALRM,
                  lambda signum, frame:
                      logger.warning("Wiki API wait time over %i, ",
                                     conf['timeout']))
    signal.alarm(conf['timeout'])    # Enable the alarm

    try:
        resp = session.get(url=url, params=params)
        signal.alarm(0)      # Disable the alarm
        return list(resp.json()['query']['pages'].values())[0]

    except requests.ConnectionError as exc:
        logger.error("Make sure you are connected to Internet.")
        return None

    except requests.RequestException as exc:
        logger.error("General Error: %s", exc)
        return None


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
    with open(args.config, 'r') as conf_file:
        conf = yaml.load(conf_file, Loader=yaml.FullLoader)

    NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
    if (NEWS_API_KEY is None) or (NEWS_API_KEY == ''):
        raise Exception('No API key')

    session = requests.Session()
    url = conf['news_url']
    params = conf['news_top']
    params['apiKey'] = NEWS_API_KEY

    try:
        resp = session.get(url=url, params=params, timeout=conf['timeout'])

        if resp.json()['status'] == 'error':
            logger.error("API error: %s", resp.json()['message'])
            raise Exception("API error")
        else:
            return resp.json()

    except requests.ConnectionError as exc:
        logger.error("Make sure you are connected to Internet.")
        return None

    except urllib3.exceptions.ReadTimeoutError:
        logger.warning("Timeout Error after %i seconds", conf['timeout'])
        return None

    except requests.exceptions.ReadTimeout:
        logger.warning("Timeout Error after %i seconds", conf['timeout'])
        return None

    except requests.RequestException as exc:
        logger.error("General Error: %s", str(exc))
        return None
