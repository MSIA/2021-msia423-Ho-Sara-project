import os
import unicodedata
import logging

import pandas as pd

from src.db import WikiNewsManager, create_db

logger = logging.getLogger(__name__)


class IngestManager:

    def __init__(self, file_path=None, engine_string=None):
        self.file_path = file_path
        self.engine_string = engine_string

        logger.info('init IngestManager')

    def __remove_accents(self, s):
        """ remove accents which database may not be able to handle """
        return unicodedata.normalize('NFD', s)

    def __render_text(self, text, entities):
        """ custom rendering of text with highlighted terms """
        entity_locs = []
        for ent in entities:
            if ' (organization)' in ent:
                ent = ent.replace(' (organization)', '')
            text = text.replace(ent, f'<span class="highlight">{ent}</span>')
        return text

    def __ingest_wiki(self, wiki_df):
        """ ingest wiki dataframe """

        tm = WikiNewsManager(engine_string=self.engine_string)
        for _, row in wiki_df.iterrows():
            date, news_id, title, wiki, url, image = row
            tm.add_wiki(date, news_id, title, wiki, url, image)
        logger.info(f"{len(wiki_df)} rows added to 'wiki' table")
        tm.close()

    def __ingest_news(self, news_df, df):
        """ ingest news dataframe """

        tm = WikiNewsManager(engine_string=self.engine_string)
        for _, row in news_df.iterrows():
            date, news_id, headline, news, image, url = row

            entities = df.loc[df['news_id'] == news_id, 'entity']. \
                drop_duplicates().values
            news_dis = self.__render_text(news, entities)

            tm.add_news(date, news_id, headline, news, news_dis, image, url)
        logger.info(f"{len(news_df)} rows  added to 'news' table")
        tm.close()

    def ingest(self):
        """after data is joined and filtered, ingest to database

        Args:
            file_path (str): file_path referencing output from filter_algo()
            enging_string (str): file_path referencing output from filter_algo()
        """
        df = pd.read_csv(self.file_path)
        df = df.fillna('')

        # when accents are removed, the primary keys may no longer be unique
        df['title'] = df['title'].apply(self.__remove_accents)
        df = df.drop_duplicates(['news_id', 'entity', 'title'])

        wiki_df = df[['date', 'news_id', 'title', 'wiki', 'wiki_url', 'wiki_image']].drop_duplicates()
        self.__ingest_wiki(wiki_df)

        news_df = df[['date', 'news_id', 'headline', 'news', 'news_image', 'news_url']].drop_duplicates()
        self.__ingest_news(news_df, df)
