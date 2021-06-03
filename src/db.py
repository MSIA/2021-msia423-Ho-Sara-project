from datetime import datetime
import logging
import logging.config

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
            self.db = SQLAlchemy(app)
            self.session = self.db.session
        if engine_string:
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
        logger.debug(f"'{title}' added to database corresponding ",
                     "to news_id {str(news_id)}")
