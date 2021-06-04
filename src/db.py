from datetime import datetime
import logging
import logging.config

import pandas as pd
from unidecode import unidecode
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, MetaData
from sqlalchemy.orm import sessionmaker
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)

Base = declarative_base()


class Wiki(Base):
    """Create schema for wiki data"""

    __tablename__ = 'wiki'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    news_id = Column(Integer)
    entity = Column(String(100))
    title = Column(String(100), unique=False)
    wiki = Column(String(10000), unique=False, nullable=False)
    wiki_url = Column(String(1000), unique=False, nullable=False)
    wiki_image = Column(String(1000), unique=False, nullable=True)

    def __repr__(self):
        return '<Wiki title: %r>' % self.title


class News(Base):
    """Create schema for news data"""

    __tablename__ = 'news'

    date = Column(DateTime, primary_key=True)
    news_id = Column(Integer, primary_key=True)
    headline = Column(String(1000), unique=False, nullable=False)
    news = Column(String(10000), unique=False, nullable=False)
    news_dis = Column(String(10000), unique=False, nullable=False)
    news_image = Column(String(1000), unique=False, nullable=False)
    news_url = Column(String(1000), unique=False, nullable=False)

    def __repr__(self):
        return '<News id %r>' % self.news_id


def drop_ifexists(engine_string, table_name):
    """Drop a table via engine_string if it exists
    to make way for ingesting new data
    """
    engine = sqlalchemy.create_engine(engine_string)
    base = declarative_base()
    metadata = MetaData(engine, reflect=True)

    table = metadata.tables.get(table_name)
    if table is not None:
        logger.info(f'Deleting {table_name} table')
        base.metadata.drop_all(engine, [table], checkfirst=True)


def create_db(engine_string: str) -> None:
    """Create database from provided engine string
    sqlite or rds instance engine
    """
    engine = sqlalchemy.create_engine(engine_string)

    drop_ifexists(engine_string, 'wiki')
    drop_ifexists(engine_string, 'news')

    Base.metadata.create_all(engine)
    logger.info("Database created.")


class WikiNewsManager:

    def __init__(self, app=None, engine_string=None):
        """
        Args:
            app: Flask - Flask app
            engine_string: str - Engine string
        """
        if app:
            logger.info('using WikiNewsManager for app')
            self.db = SQLAlchemy(app)
            self.session = self.db.session
        if engine_string:
            logger.info('using WikiNewsManager for db')
            engine = sqlalchemy.create_engine(engine_string)
            Session = sessionmaker(bind=engine)
            self.session = Session()
        else:
            raise ValueError("Need either an engine string",
                             "or a Flask app to initialize")

    def close(self) -> None:
        """Closes session"""
        self.session.close()

    def add_news(self, date: datetime,
                 news_id: int, headline: str, news: str, news_dis: str,
                 img: str, url: str) -> None:
        """Seeds an existing database with additional news.
        Args:
            date: `datetime` of day that the headlines are downloaded
            news_id: `int` index of the headline for the daily news
            news: `str` headline and description the news API
        """

        session = self.session
        news_record = News(date=datetime.strptime(date, '%b-%d-%Y'),
                           news_id=news_id,
                           headline=headline,
                           news=news,
                           news_dis=news_dis,
                           news_image=img,
                           news_url=url)
        session.add(news_record)
        session.commit()
        logger.debug(f"'{news[0:20]}' added to db with id {str(news_id)}")

    def add_wiki(self, date: datetime, news_id: int, title: str,
                 wiki: str, url: str, img: str) -> None:
        """Seeds an existing database with additional wiki recommendations"""

        session = self.session
        wiki_record = Wiki(date=datetime.strptime(date, '%b-%d-%Y'),
                           news_id=news_id,
                           title=title,
                           wiki=wiki,
                           wiki_url=url,
                           wiki_image=img)

        session.add(wiki_record)
        session.commit()
        logger.debug(f"'{title}' added to db ~ for news_id {str(news_id)}")


def remove_accents(s):
    """ remove accents which database may not be able to handle """
    return unidecode(s)


def render_text(text, entities):
    """ custom rendering of text with highlighted terms """
    entity_locs = []
    for ent in entities:
        if ' (organization)' in ent:
            ent = ent.replace(' (organization)', '')
        text = text.replace(ent, f'<span class="highlight">{ent}</span>')
    return text


def ingest_wiki(wiki_df, engine_string):
    """ ingest wiki dataframe """

    tm = WikiNewsManager(app=None, engine_string=engine_string)
    for _, row in wiki_df.iterrows():
        date, news_id, title, wiki, url, image = row
        tm.add_wiki(date, news_id, title, wiki, url, image)
    logger.info(f"{len(wiki_df)} rows added to 'wiki' table")
    tm.close()


def render_news_col(news_df, df):
    """ ingest news dataframe """
    news_df['news_dis'] = ''
    news_obs = news_df['news'].unique()

    for i, row in news_df.iterrows():
        date, news_id, headline, news, image, url, _ = row
        entities = df.loc[df['news_id'] == news_id, 'entity']. \
            drop_duplicates().values
        news_df.loc[i, 'news_dis'] = render_text(news, entities)
    return news_df


def ingest_news(news_df, engine_string):
    """ ingest news dataframe """

    tm = WikiNewsManager(app=None, engine_string=engine_string)
    for _, row in news_df.iterrows():
        date, news_id, headline, news, image, url, news_dis = row
        tm.add_news(date, news_id, headline, news, news_dis, image, url)
    logger.info(f"{len(news_df)} rows  added to 'news' table")
    tm.close()


def ingest(file_path, engine_string):
    """after data is joined and filtered, ingest to database

    Args:
        file_path (str): file_path referencing output from filter_algo()
        enging_string (str): file_path referencing output from filter_algo()
    """
    df = pd.read_csv(file_path)
    df = df.fillna('')

    # when accents are removed, the primary keys may no longer be unique
    df['title'] = df['title'].apply(remove_accents)
    df = df.drop_duplicates(['news_id', 'entity', 'title'])

    wiki_df = df[['date', 'news_id', 'title', 'wiki', 'wiki_url', 'wiki_image']] \
        .drop_duplicates()
    ingest_wiki(wiki_df, engine_string)

    news_df = df[['date', 'news_id', 'headline', 'news', 'news_image', 'news_url']] \
        .drop_duplicates()
    news_df = render_news_col(news_df, df)
    ingest_news(news_df, engine_string)
