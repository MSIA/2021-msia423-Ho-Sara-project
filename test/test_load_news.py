import sys
import os
import pandas as pd
from numpy import array

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
from load_news import create_id_col, remove_stopwords


def create_id_col(data, id_col):
    if id_col in data.columns:
        return data

    data.reset_index(inplace=True)
    data.rename(columns={'index': id_col}, inplace=True)
    return data


def remove_stopwords(text, stopwords):
    for word in stopwords:
        text = text.replace(word, '')
    return text
