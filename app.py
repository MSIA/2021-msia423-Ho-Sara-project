import os
import traceback
import logging.config

from flask import Flask
from flask import render_template, request, redirect, url_for

# Initialize the database session
from src.add_records import Wiki, News, WikiNewsManager

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
        logger.debug("Index page accessed")
        return render_template('index.html', wiki_entities=wiki_entities)
    except:
        traceback.print_exc()
        logger.warning("Not able to display wikinews, error page returned")
        return render_template('error.html')


if __name__ == '__main__':
    app.run(debug=app.config["DEBUG"], 
            port=app.config["PORT"], 
            host=app.config["HOST"])
