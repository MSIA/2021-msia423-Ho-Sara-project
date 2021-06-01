import os
import unicodedata
import logging
import logging.config

import pandas as pd
from spacy import displacy

from src.db import WikiNewsManager, create_db

logging.config.fileConfig("config/logging/local.conf",
                          disable_existing_loggers=False)
logger = logging.getLogger(__name__)


def remove_accents(s):
    """ remove accents which certain databases may not be able to handle """
    return unicodedata.normalize('NFD', s)


def render_text(text, entities):
    """ custom spacy-style rendering of text with highlighted terms """
    entity_locs = []
    for ent in entities:
        if ' (organization)' in ent:
            ent = ent.replace(' (organization)', '')
        start = text.find(ent)
        end = start + len(ent)
        entity_locs.append({'start': start, 'end': end, 'label': ''})

    colors = {"": "linear-gradient(90deg, #a2dff0, #b1d3ae)"}
    options = {"ents": [""], "colors": colors}

    doc = [{"text": text,
            "ents": entity_locs,
            "title": None}]
    return displacy.render(doc, style="ent", jupyter=False, manual=True, options=options)


def ingest_wiki(wiki_df, engine_string):
    """ ingest wiki dataframe """

    tm = WikiNewsManager(engine_string=engine_string)
    for _, row in wiki_df.iterrows():
        date, news_id, title, wiki, url, image = row
        tm.add_wiki(date, news_id, title, wiki, url, image)
    logger.info(f"{len(wiki_df)} rows added to 'wiki' table")
    tm.close()


def ingest_news(news_df, df, engine_string):
    """ ingest news dataframe """

    tm = WikiNewsManager(engine_string=engine_string)
    for _, row in news_df.iterrows():
        date, news_id, news, image, url = row

        entities = df.loc[df['news_id'] == news_id, 'entity'].drop_duplicates().values
        news_dis = render_text(news, entities)

        tm.add_news(date, news_id, news, news_dis, image, url)
    logger.info(f"{len(news_df)} rows  added to 'news' table")
    tm.close()


def ingest(file_path, engine_string):
    """after data is joined and filtered, ingest to database

    Args:
        df (obj `pandas.DataFrame`): output from filter_algo()
    """
    df = pd.read_csv(file_path)
    df = df.fillna('')

    # when accents are removed, the primary keys may no longer be unique
    df['title'] = df['title'].apply(remove_accents)
    df = df.drop_duplicates(['news_id', 'entity', 'title'])

    wiki_df = df[['date', 'news_id', 'title', 'wiki', 'wiki_url', 'wiki_image']].drop_duplicates()
    ingest_wiki(wiki_df, engine_string)

    news_df = df[['date', 'news_id', 'news', 'news_image', 'news_url']].drop_duplicates()
    ingest_news(news_df, df, engine_string)
