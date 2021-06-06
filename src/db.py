from datetime import datetime
import logging
import logging.config
import traceback

import pandas as pd
from unidecode import unidecode
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, MetaData, Text, Table
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
    wiki = Column(Text(10000), unique=False, nullable=False)
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
    news = Column(Text(10000), unique=False, nullable=False)
    news_dis = Column(Text(10000), unique=False, nullable=False)
    news_image = Column(String(1000), unique=False, nullable=False)
    news_url = Column(String(1000), unique=False, nullable=False)

    def __repr__(self):
        return '<News id %r>' % self.news_id


class WikiNewsManager:

    def __init__(self, app=None, engine_string=None):
        """
        Args:
            app (obj): flask app
            engine_string (str): engine string referring to database
        """
        if app:
            logger.info('using WikiNewsManager for app')
            self.db = SQLAlchemy(app)
            self.session = self.db.session
        elif engine_string:
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
        """Seeds an existing database with news"""

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
        logger.debug(f"'%s' added to db with id %i",
                     (news[0:20], news_id))

    def add_wiki(self, date: datetime, news_id: int, title: str,
                 wiki: str, url: str, img: str) -> None:
        """Seeds an existing database with wiki recommendations"""

        session = self.session
        wiki_record = Wiki(date=datetime.strptime(date, '%b-%d-%Y'),
                           news_id=news_id,
                           title=title,
                           wiki=wiki,
                           wiki_url=url,
                           wiki_image=img)

        session.add(wiki_record)
        session.commit()
        logger.debug(f"'%s' added to db ~ for news_id %i",
                     (title, news_id))


def delete_ifexists(engine_string, table_name) -> None:
    """Deletes rows in table to make way for new daily data

    Args:
        engine_string (str): engine string referring to database
        table_name (str): name of table in database
    """
    engine = sqlalchemy.create_engine(engine_string)

    Session = sessionmaker(bind=engine)
    session = Session()

    metadata = MetaData()
    metadata.reflect(bind=engine)

    inspector = sqlalchemy.inspect(engine)
    if table_name in inspector.get_table_names():
        try:
            logger.debug('Try deleting rows from table %s', {table_name})
            table = Table(table_name, metadata, autoload_with=engine)
            session.query(table).delete(synchronize_session=False)
            session.commit()
            logger.debug('Successfully rows from  table %s', {table_name})
        except:
            logger.warning('Could not delete rows from %s', {table_name})
            traceback.print_exc()
            session.rollback()


def create_db(engine_string: str) -> None:
    """Create database from provided engine string
    sqlite or rds instance engine
    """
    if 'aws.com' in engine_string:
        logger.debug("connecting to AWS engine string")
    else:
        logger.debug("connecting to non-AWS engine string")

    engine = sqlalchemy.create_engine(engine_string)

    delete_ifexists(engine_string, 'wiki')
    delete_ifexists(engine_string, 'news')

    Base.metadata.create_all(engine)
    logger.info("Database created.")


def render_text(text, entities):
    """Add html class "highlight" to substrings in the text

    Args:
        text (str): text with substrings that need to be highlighted
        entities (array-like): list of substrings to highlight

    Returns:
        str: text formatted for html
    """
    entity_locs = []
    for ent in entities:
        if ' (organization)' in ent:
            ent = ent.replace(' (organization)', '')
        text = text.replace(ent, f'<span class="highlight">{ent}</span>')
    return text


def render_news_col(news_df, df, args):
    """Add html class "highlight" to substrings in the text

    Args:
        news_df (obj `pandas.DataFrame`):
            dataframe with `news` column with substrings to be highlighted
        df (obj `pandas.DataFrame`):
            dataframe with which can be merged with news_df to find entities
        args (dict): yaml-style config with keys:
            'raw_column', 'new_column', 'entity_column'

    Returns:
        obj `pandas.DataFrame`: with column 'news_dis' formatted for html
    """

    news_df[args['new_column']] = ''
    news_obs = news_df[args['raw_column']].unique()

    for i, row in news_df.iterrows():
        date, news_id, headline, news, image, url, _ = row
        entities = df.loc[df['news_id'] == news_id, args['entity_column']]. \
            drop_duplicates().values
        news_df.loc[i, args['new_column']] = render_text(news, entities)
    return news_df


def ingest_wiki(wiki_df, engine_string) -> None:
    """Ingest wiki dataframe to database

    Args:
        wiki_df (obj `pandas.DataFrame`): with the following columns
            date, news_id, title, wiki, url, image
        engine_string (str): engine string for database
    """

    tm = WikiNewsManager(app=None, engine_string=engine_string)
    for _, row in wiki_df.iterrows():
        date, news_id, title, wiki, url, image = row
        tm.add_wiki(date, news_id, title, wiki, url, image)
    logger.info("%i rows added to 'wiki' table", {len(wiki_df)})
    tm.close()


def ingest_news(news_df, engine_string) -> None:
    """Ingest news dataframe to database

    Args:
        news_df (obj `pandas.DataFrame`): with the following columns
            date, news_id, headline, news, image, url, news_dis
        engine_string (str): engine string for database
    """

    tm = WikiNewsManager(app=None, engine_string=engine_string)
    for _, row in news_df.iterrows():
        date, news_id, headline, news, image, url, news_dis = row
        tm.add_news(date, news_id, headline, news, news_dis, image, url)
    logger.info("%i rows  added to 'news' table", {len(news_df)})
    tm.close()


def remove_accents(s):
    """ remove accents which database may not be able to handle """
    return unidecode(s)


def normalize(df, args):
    """normalizes non-utf chars in a primary key to avoid nonunique errors

    Args:
        df (obj `pandas.DataFrame`)
        args (dict): yaml-style config with keys:
            'primary_key', 'primary_keys'
    """

    df[args['primary_key']] = df[args['primary_key']].apply(remove_accents)
    # when accents are removed, the primary keys may no longer be unique
    df = df.drop_duplicates(args['primary_keys'])
    return df


def ingest(file_path, engine_string, args) -> None:
    """Orchestration function; after data is joined and filtered, ingest to db

    Args:
        file_path (str): file_path referencing output from filter_data()
        engine_string (str): engine string for database
        args (dict): yaml-style config with:
            args['normalize']['primary_key']
            args['normalize']['primary_keys']
            args['news']['raw_columns']
            args['wiki']['raw_columns']
            args['render']
    """

    df = pd.read_csv(file_path)
    df = df.fillna('')

    if 'normalize' in args:
        df = normalize(df, args['normalize'])

    wiki_df = df[args['wiki']['raw_columns']] \
        .drop_duplicates()
    ingest_wiki(wiki_df, engine_string)

    news_df = df[args['news']['raw_columns']] \
        .drop_duplicates()
    news_df = render_news_col(news_df, df, args['render'])
    ingest_news(news_df, engine_string)
