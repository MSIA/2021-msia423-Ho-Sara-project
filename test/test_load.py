import sys
import os
import pandas as pd
from numpy import array

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
from load import news2entities


def test_news2entities():
    c = {'spacy_model': 'en_core_web_sm',
         'stop_spacy': ['PERSON', 'FAC', 'ORG', 'NORP', 'PRODUCT']}

    sample_string = """
        Nigeria Suspends Twitter After It Deleted A Tweet By The President
         - Twitter deleted Muhammadu Buhari's post on Wednesday, calling
        it abusive, after the president threatened suspected separatist
        militants in the southeast.
        """
    test_out = news2entities(sample_string, c)
    true_out = ['Suspends Twitter', "Muhammadu Buhari's"]
    assert test_out == true_out
