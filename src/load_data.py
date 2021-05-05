from datetime import date
import spacy
import pandas as pd

from api_helpers import *
from sim import *

nlp = spacy.load("en_core_web_sm")


def load_news():
    print('loading news')
    data = news_top()
    news = []
    for article in data['articles']:

        headline = article['title']
        if article['description'] is not None:
            headline += article['description']

        # remove publication information
        headline = headline.replace(article['source']['name'], '')
        news.append(headline)

    news_table = pd.DataFrame(news).reset_index()
    news_table.columns = ['news_id', 'news']

    today = date.today().strftime("%b-%d-%Y")
    news_table.to_csv(f'./data/{today}-us-top-headlines.csv', index=False)
    return news_table


def load_wiki(news_table):
    print('matching news with wiki entries')
    table_data = []
    for _, row in news_table.iterrows():
        news_id, news = row

        print('------------------')
        print(news)

        # start to break query into named entities
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

        for ent, label in zip(entities, labels):
            articledata = wiki_query(ent)

            try:
                search_results = articledata['query']['search']

                for result in search_results[0:3]:  # take the top 3
                    title = result['title']
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
                            image = ''
                        table_data.append({'news_id': news_id,
                                           'entity': ent,
                                           'label': label,
                                           'title': info['title'],
                                           'category': categories[0],
                                           'revised': info['touched'],
                                           'url': info['fullurl'],
                                           'wiki': content['extract'],
                                           'image': image})

            except(IndexError):
                continue

    table = pd.DataFrame(table_data)
    today = date.today().strftime("%b-%d-%Y")
    table.to_csv(f'./data/{today}-wiki-entries-for-us-top-headlines.csv',
                 index=False)
    return table
