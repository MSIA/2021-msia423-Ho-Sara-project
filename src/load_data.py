from datetime import date
import spacy
import pandas as pd

from config import NEWS_API_KEY
from api_helpers import *
from sim import *

nlp = spacy.load("en_core_web_sm")


def load_news():
    data = news_top()
    news = []
    for article in data['articles']:
        headline = article['title']
        if article['description'] is not None:
            headline += article['description']

        headline = headline.replace(article['source']['name'], '') # remove publication information
        news.append(headline)

    news_table = pd.DataFrame(news).reset_index()
    news_table.columns = ['news_id', 'news']
    return news_table


def load_wiki(news_table):
    table_data = []
    for _, row in news_table.iterrows():
        news_id, news = row

        print('------------------')
        print(news)

        # start to break query into named entities
        doc = nlp(news)

        entities = []
        for ent in doc.ents:
            if (ent.label_ in ['PERSON', 'FAC', 'ORG', 'NORP', 'PRODUCT']) and (ent.text not in entities):
                if ent.label_ == 'PERSON':
                    label = 'PERSON'
                elif ent.label_ == 'NORP':
                    label = 'GROUP'
                elif ent.label_ == 'ORG':
                    label = 'ORGANIZATION'
                else:
                    label = ''

            articledata = wiki_query(ent.text + label)

            try: 
                search_results = articledata['query']['search']
                i = 0
                while((i < len(search_results)) & (distance(ent.text, search_results[i]['title']) < 10)):
                    title = search_results[i]['title']
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
                            image = None
                        table_data.append({'news_id': qid,
                                           'entity': ent.text,
                                           'label': label,
                                           'title': info['title'],
                                           'category': categories[0],
                                           'revised': info['touched'],
                                           'url': info['fullurl'],
                                           'wiki': content['extract'],
                                           'image': image})
                    i += 1

            except(IndexError):
                continue

    # today = date.today().strftime("%b-%d-%Y")
    # table.to_csv(f'{today}-us-top-headlines.csv', index = False)
    return pd.DataFrame(table_data)
