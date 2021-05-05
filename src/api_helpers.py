import requests
from config import NEWS_API_KEY

def wiki_query(query):
    S = requests.Session()
    URL = "https://en.wikipedia.org/w/api.php"

    PARAMS = {'action': 'query',
              'format': 'json',
              'list': 'search',
              'srsearch': query}

    R = S.get(url=URL, params=PARAMS)
    return R.json()


def wiki_pagecontent(title):
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


def news_query(query):
    S = requests.Session()
    URL = "https://newsapi.org/v2/everything?"
    PARAMS = {'apiKey': NEWS_API_KEY,
              'q': query,
              'from': '2021-04-04',
              'to': '2021-04-05'}
    S.get(url=URL, params=PARAMS)

    R = S.get(url=URL, params=PARAMS)
    return R.json()


def news_top():
    S = requests.Session()
    URL = "https://newsapi.org/v2/top-headlines?"
    PARAMS = {'apiKey': NEWS_API_KEY,
              'country': 'us',
              'pagesize': 100}
    S.get(url=URL, params=PARAMS)

    R = S.get(url=URL, params=PARAMS)
    return R.json()
