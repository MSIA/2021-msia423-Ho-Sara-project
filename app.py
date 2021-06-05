import os
import traceback
import logging.config

from flask import Flask
from flask import render_template, request, redirect, url_for
from config.flaskconfig import *

# Initialize the database session
from src.db import Wiki, News, WikiNewsManager
from config.flaskconfig import SQLALCHEMY_DATABASE_URI

# Initialize the Flask application
app = Flask(__name__,
            template_folder="app/templates",
            static_folder="app/static")

# Configure flask app from flask_config.py
app.config.from_pyfile('config/flaskconfig.py')

logging.config.fileConfig(app.config["LOGGING_CONFIG"])
logger = logging.getLogger(app.config["APP_NAME"])

manager = WikiNewsManager(engine_string=SQLALCHEMY_DATABASE_URI)

@app.route('/')
def index():
    """Main view that lists some news headlines
    and associated wikipedia articles.

    Create view into index page that uses data queried from entries database
    inserts it into the ./templates/index.html template.

    Returns: rendered html template
    """

    try:
        date = manager.session.query(News.date).distinct().first()[0]
        date = date.strftime('%b-%d-%Y')
        wiki_entities = manager.session.query(Wiki).all()
        news_entities = manager.session.query(News).all()

        logger.debug("Index page accessed")
        return render_template('index.html',
                               date=date,
                               wiki_entities=wiki_entities,
                               news_entities=news_entities)
    except:
        logger.debug("session.rollback() invoked")
        manager.session.rollback()

        traceback.print_exc()
        logger.warning("Not able to display wikinews, error page returned")
        return render_template('error.html')


if __name__ == '__main__':
    app.run(debug=app.config["DEBUG"],
            port=app.config["PORT"],
            host=app.config["HOST"])
