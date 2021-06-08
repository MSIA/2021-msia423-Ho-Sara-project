"""Module containing functions to load and process wiki API data

Orchestration functions:
    load_wiki(news_table, query_conf, content_conf,
              stop_spacy, spacy_model,
              stop_categories, stop_phrases, n_results)
    news2entities(news, stop_spacy, spacy_model)
    entities2wiki(entities, query_conf, content_conf,
                  stop_categories, stop_phrases, n_results)

Helper functions for parsing JSON data:
    wiki_special_truncate(text)
    wiki_image(data)

Helper functions for making API calls:
    wiki_query(conf, query, timeout)
    wiki_page_content(conf, title, timeout)
"""

import logging
import logging.config
import signal
import urllib3

import requests
import pandas as pd
import spacy

logging.config.fileConfig("config/logging/local.conf",
                          disable_existing_loggers=False)
logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def load_wiki(news_table, query_conf, content_conf,
              stop_spacy=[], spacy_model='en_core_web_sm',
              stop_categories=[], stop_phrases=[], n_results=1):
    """Orchestration function which matches news with wikipedia articles

    Args:
        news_table (obj `pandas.DataFrame`)
        query_conf (dict): configuration for wiki_query()
        content_conf (dict): configuration for wiki_content()
        stop_spacy (array-like): types of entities to ignore. Defaults to [].
        spacy_model (str): model name; Defaults to 'en_core_web_sm'
            see https://spacy.io/usage/models.
        stop_categories (list, optional): categories to filter out. Defaults to []
        stop_phrases (list, optional): phrases to filter out. Defaults to []
        n_results (int, optional): number of suggested articles to consider. Defaults to 1

    Returns:
        obj `pandas.DataFrame`
    """

    logger.info('matching news with wiki entries from Wikipedia API')

    wiki_data = []
    for _, row in news_table[['news_id', 'news']].iterrows():
        news_id, news = row

        logger.info("----Processing '%s...'", news[0:25])

        entities = news2entities(news, stop_spacy, spacy_model)
        wiki_obs = entities2wiki(entities,
                                 query_conf,
                                 content_conf,
                                 stop_categories,
                                 stop_phrases,
                                 n_results)
        wiki_obs['news_id'] = news_id
        wiki_data.append(wiki_obs)

    return pd.concat(wiki_data)


def news2entities(news, stop_spacy, spacy_model):
    """Run spacy model on news; returns entities

    Args:
        news (str): news headline
        stop_spacy (array-like): types of entities to ignore. Defaults to []
        spacy_model (str): model name; see https://spacy.io/usage/models

    Returns:
        (list): list of entities suggested by spacy model
    """

    nlp = spacy.load(spacy_model)
    doc = nlp(news)

    entities = []
    for ent in doc.ents:
        if (ent.label_ in stop_spacy) and (ent.text not in entities):
            text = ent.text
            if ent.label_ == 'ORG':
                text += ' (organization)'
            entities.append(text)

    return entities


def entities2wiki(entities, query_conf, content_conf,
                  stop_categories=[], stop_phrases=[], n_results=1):
    """Orchestration function to return clean wikipedia information for a series of entities

    Args:
        entities (array like): list of entities; output from news2entities
        query_conf (dict): configuration for wiki_query()
        content_conf (dict): configuration for wiki_content()
        stop_categories (list, optional): categories to filter out. Defaults to []
        stop_phrases (list, optional): phrases to filter out. Defaults to []
        n_results (int, optional): number of suggested articles to consider. Defaults to 1

    Returns:
        [type]: [description]
    """
    all_data = []
    all_titles = []
    for ent in entities:
        articledata = wiki_query(query_conf, ent)
        search_results = articledata['query']['search']

        # n_results is how many search results to consider matching
        for result in search_results[0:n_results]:

            title = result['title']
            if title in all_titles:
                logger.debug('%s has already been added', title)
                continue        # bypass the rest of the for loop

            info = wiki_content(content_conf, title)
            try:
                categories = info['categories']
                categories = [kv['title'].lower() for kv in categories]
                if set(categories) & set(stop_categories):
                    continue     # bypass the rest of the for loop

            except KeyError:
                pass             # bypass the rest of the for loop

            wiki = info['extract']
            if set(stop_phrases) & set(wiki.lower().split()):
                continue     # bypass the rest of the for loop

            wiki = wiki_special_truncate(wiki)
            image = wiki_image(info)

            logger.info("%s found as a match", info['title'])
            all_titles.append(title)
            all_data.append({'entity': ent,
                             'title': info['title'],
                             'wiki': wiki,
                             'wiki_url': info['fullurl'],
                             'wiki_image': image})

    return pd.DataFrame(all_data)

def wiki_special_truncate(text):
    """'==' denotes a special section break. Truncate the Wikipedia content here"""

    if '==' in text:
        end = text.find('==')
        return text[0:end]
    return text


def wiki_image(data):
    """returns thumbnail url if there exists one in the JSON data"""

    try:
        return data['thumbnail']['source']
    except KeyError:
        return ''


def wiki_query(conf, query, timeout=300):
    """Given a search query, returns suggestions from Wikipedia's search engine

    Args:
        conf (dict): configuration containing:
            'url': url for `session.get()`
            'params': params for `session.get()` containing:
                see https://www.mediawiki.org/wiki/API:Query for more params
        query (text): an entity suggested from the news headlines
        timeout (int): how long to wait for response before timing out. Default 300 seconds

    Returns:
        object: `JSON` formatted data
    """

    session = requests.Session()
    url = conf['url']
    params = conf['params']
    params['srsearch'] = query  # add query to the parameters, required by API

    try:
        return session.get(url=url,
                           params=params,
                           timeout=timeout).json()

    except requests.ConnectionError:
        logger.error("Make sure you are connected to Internet.")
        return None

    except urllib3.exceptions.ReadTimeoutError:
        logger.warning("Timeout Error after %i seconds", timeout)
        return None

    except requests.exceptions.ReadTimeout:
        logger.warning("Timeout Error after %i seconds", timeout)
        return None

    except requests.RequestException as exc:
        logger.error("General Error: %s", exc)
        return None


def wiki_content(conf, title, timeout=300):
    """Given an article title, returns page info

    Args:
        conf (dict): configuration containing:
            'url': url for `session.get()`
            'params': params for `session.get()` containing:
                see https://www.mediawiki.org/wiki/API:Query for more params
        query (text): an entity suggested from the news headlines
        timeout (int): how long to wait for response before timing out. Default 300 seconds

    Returns:
        object: `JSON` formatted data
    """

    logger.debug("gathering pagecontent for page %s", title)

    session = requests.Session()
    url = conf['url']
    params = conf['params']
    params['titles'] = title  # add title to the parameters, required by API

    signal.signal(signal.SIGALRM,
                  lambda signum, frame:
                      logger.warning("Wiki API wait time over %i, ",
                                     timeout))
    signal.alarm(timeout)    # Enable the alarm

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
