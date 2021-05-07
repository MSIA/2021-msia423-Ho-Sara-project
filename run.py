import os
import argparse
import logging.config
from datetime import datetime
import unicodedata


from datetime import date
import pandas as pd

from src.add_records import WikiNewsManager, create_db
from config.flaskconfig import SQLALCHEMY_DATABASE_URI

logging.config.fileConfig('config/logging/local.conf')
logger = logging.getLogger('wikinews-pipeline')


if __name__ == '__main__':

    # Add parsers for both creating a database and adding songs to it
    parser = argparse.ArgumentParser(description="Create and/or add data to database")
    subparsers = parser.add_subparsers(dest='subparser_name')

    # Sub-parser for creating a database
    sb_create = subparsers.add_parser("create_db", description="Create database")
    sb_create.add_argument("--engine_string", default=SQLALCHEMY_DATABASE_URI,
                           help="SQLAlchemy connection URI for database")

    # Sub-parser for ingesting new data
    sb_ingest = subparsers.add_parser("ingest", description="Add data to database")
    sb_ingest.add_argument("--engine_string", default='sqlite:///data/entries.db',
                           help="SQLAlchemy connection URI for database")

    args = parser.parse_args()
    sp_used = args.subparser_name
    if sp_used == 'create_db':
        create_db(args.engine_string)
    elif sp_used == 'ingest':
        tm = WikiNewsManager(engine_string=args.engine_string)

        for file in os.listdir('./data/sample'):
            if 'wiki-entries' in file:
                wiki_table = pd.read_csv(f'./data/sample/{file}')
                wiki_table = wiki_table.fillna('')
                def remove_accents(s):
                    return unicodedata.normalize('NFD', s)

                wiki_table['title'] = wiki_table['title'].apply(remove_accents)

                wiki_table = wiki_table.drop_duplicates(['news_id', 'entity', 'title'])

                file_date = ('-').join(file.split('-')[0:3])
                file_date = datetime.strptime(file_date, '%b-%d-%Y')

                for _, row in wiki_table.iterrows():
                    news_id, entity, label, title, category, revised, url, wiki, image = row
                    tm.add_wiki(file_date, news_id, entity, label,
                                title, category, revised,
                                url, wiki, image)
                logger.info(f"data in {file} added to 'wiki' table")

            elif '.csv' in file:
                news_table = pd.read_csv(f'./data/sample/{file}')
                news_table = news_table.fillna('')
                file_date = ('-').join(file.split('-')[0:3])
                file_date = datetime.strptime(file_date, '%b-%d-%Y')

                for _, row in news_table.iterrows():
                    news_id, news = row
                    tm.add_news(file_date, news_id, news)
                logger.info(f"data in {file} added to 'news' table")

            tm.close()
    else:
        parser.print_help()
