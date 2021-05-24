import os
import traceback
import logging.config

from flask import Flask
from flask import render_template, request, redirect, url_for
from config.flaskconfig import *

# Initialize the database session
from src.add_entries import Wiki, News, WikiNewsManager

# Initialize the Flask application
app = Flask(__name__, 
            template_folder="app/templates", 
            static_folder="app/static")

# Configure flask app from flask_config.py
app.config.from_pyfile('config/flaskconfig.py')

# Define LOGGING_CONFIG in flask_config.py - path to config file for setting
# up the logger (e.g. config/logging/local.conf)
logging.config.fileConfig(app.config["LOGGING_CONFIG"])
logger = logging.getLogger(app.config["APP_NAME"])
db = 'sqlite:///data/entries.db'
# db = f'{DB_DIALECT}://{DB_USER}:{DB_PW}@{DB_HOST}:{DB_PORT}/{DATABASE}'
logger.debug('Web app log')

manager = WikiNewsManager(engine_string=db)

@app.route('/')
def index():
    """Main view that lists some news headlines
    and associated wikipedia articles.

    Create view into index page that uses data queried from entries database
    inserts it into the ./templates/index.html template.

    Returns: rendered html template

    """

    try:
        wiki_entities = manager.session.query(Wiki).all()
        news_entities = manager.session.query(News).all()


        print(wiki_entities)
        logger.debug("Index page accessed")
        return render_template('index.html', 
            wiki_entities=wiki_entities,
            news_entities=news_entities)
    except:
        traceback.print_exc()
        logger.warning("Not able to display wikinews, error page returned")
        return render_template('error.html')


if __name__ == '__main__':
    app.run(debug=app.config["DEBUG"],
            port=app.config["PORT"],
            host=app.config["HOST"])
