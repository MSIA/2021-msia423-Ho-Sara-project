"""Web app serving filtered news and wiki matches

@app.route('/')
def index(): returns main homepage with data queried from database

@app.route('/about')
def about(): returns about homepage with static information
"""

import traceback
import logging.config

import sqlalchemy
from flask import Flask
from flask import render_template

from src.db import Wiki, News, WikiNewsManager
from config.db_config import ENGINE_STRING

# Initialize the Flask application
app = Flask(__name__,
            template_folder="app/templates",
            static_folder="app/static")

# Configure flask app from flask_config.py
app.config.from_pyfile('config/flask_config.py')
logging.config.fileConfig(app.config["LOGGING_CONFIG"])
logger = logging.getLogger(app.config["APP_NAME"])

manager = WikiNewsManager(engine_string=ENGINE_STRING)
wn_session = manager.session


@app.route('/')
def index():
    """Main view that lists some news headlines
    and associated wikipedia articles.

    Create view into index page that uses data queried from entries database
    inserts it into the ./templates/index.html template.

    Returns: rendered html template
    """
    if 'aws.com' in ENGINE_STRING:
        logger.debug("connecting to AWS engine string")
    else:
        logger.debug("connecting to non-AWS engine string")

    try:
        date = wn_session.query(News.date).distinct().first()[0]
        date = date.strftime('%b-%d-%Y')

        wiki_entities = wn_session.query(Wiki).all()
        news_entities = wn_session.query(News).all()

        logger.debug("Index page accessed")
        return render_template('index.html',
                               date=date,
                               wiki_entities=wiki_entities,
                               news_entities=news_entities)

    # should handle *any* exceptions to avoid front-end errors in deployed app
    except:
        logger.debug("session.rollback() invoked")
        wn_session.rollback()

        traceback.print_exc()
        logger.warning("Not able to display wikinews, error page returned")
        return render_template('error.html')


@app.route('/about')
def about():
    """render about.html"""
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=app.config["DEBUG"],
            port=app.config["PORT"],
            host=app.config["HOST"])
