import logging.config

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, MetaData
from sqlalchemy.orm import sessionmaker
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)
logger.setLevel("INFO")

Base = declarative_base()


class Wiki(Base):
    """Create a data model for the database to be set up for loading wiki data
    """

    __tablename__ = 'wiki'

    news_id = Column(Integer, primary_key=True)
    entity = Column(String(100), primary_key=True)
    label = Column(String(100), unique=False, nullable=False)
    title = Column(String(100), unique=False, nullable=False)
    category = Column(String(100), unique=False, nullable=True)
    revised = Column(String(100), unique=False, nullable=False)
    url = Column(String(100), unique=False, nullable=False)
    wiki = Column(String(10000), unique=False, nullable=False)
    image = Column(String(100), unique=False, nullable=True)

    def __repr__(self):
        return '<Wiki title: %r>' % self.title


class News(Base):
    """Create a data model for the database to be set up for loading news data
    """
    __tablename__ = 'news'

    news_id = Column(Integer, primary_key=True)
    news = Column(String(10000), unique=False, nullable=False)

    def __repr__(self):
        return '<Track %r>' % self.news_id


def create_db(engine_string: str) -> None:
    """Create database from provided engine string

    Args:
        engine_string: str - Engine string

    Returns: None

    """
    engine = sqlalchemy.create_engine(engine_string)

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
        elif engine_string:
            engine = sqlalchemy.create_engine(engine_string)
            Session = sessionmaker(bind=engine)
            self.session = Session()
        else:
            raise ValueError("Need either an engine string or a Flask app to initialize")

    def close(self) -> None:
        """Closes session

        Returns: None

        """
        self.session.close()

    def add_news(self, news_id: int, news: str) -> None:
        """Seeds an existing database with additional news.

        Args:

        Returns:None

        """
        session = self.session
        news = News(news_id=news_id, news=news)
        session.add(news)
        session.commit()
        logger.info(f"'{news[0:20]}' added to database with id {str(news_id)}")


    def add_wiki(self, news_id: int, entity: str, label: str, title: str, category: str, revised: str, url: str, wiki: str, image: str) -> None:
        """Seeds an existing database with additional wiki recommendations.

        Args:

        Returns:None

        """

        session = self.session
        wiki_record = Wiki(news_id=news_id, 
                           entity=entity,
                           label=label,
                           title=title,
                           category=category,
                           revised=revised,
                           url=url,
                           wiki=wiki,
                           image=image)
        session.add(wiki_record)
        session.commit()
        logger.info(f"'{entity}' added to database corresponding to news_id {str(news_id)}")
