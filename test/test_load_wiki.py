import sys
import os
import pandas as pd
from numpy import array

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
from load_wiki import news2entities, wiki_special_truncate


def test_news2entities():
    spacy_model = 'en_core_web_sm'
    spacy_cat = ['PERSON', 'FAC', 'ORG', 'NORP', 'PRODUCT']

    sample_string = """
        Nigeria Suspends Twitter After It Deleted A Tweet By The President
         - Twitter deleted Muhammadu Buhari's post on Wednesday, calling
        it abusive, after the president threatened suspected separatist
        militants in the southeast.
        """
    test_out = news2entities(sample_string, spacy_cat, spacy_model)
    true_out = ['Suspends Twitter', "Muhammadu Buhari's"]
    assert test_out == true_out


def test_wiki_special_truncate():
    sample_string = """
    The fight ended in a majority draw. In the subsequent rematch, which was a professional bout, Paul lost to KSI by split decision.\nPaul has been involved in several controversies, most notably in relation to a trip to Japan in December 2017, during which he visited the Aokigahara "suicide forest", filmed a suicide victim and uploaded the footage to his YouTube channel.\n\n\n== Early life and education ==\nPaul grew up in Ohio with younger brother Jake, who is also a YouTuber and internet personality.',
    """
    test_out = wiki_special_truncate(sample_string)

    true_out = """
    The fight ended in a majority draw. In the subsequent rematch, which was a professional bout, Paul lost to KSI by split decision.\nPaul has been involved in several controversies, most notably in relation to a trip to Japan in December 2017, during which he visited the Aokigahara "suicide forest", filmed a suicide victim and uploaded the footage to his YouTube channel.\n\n\n== Early life and education 
    """

    assert true_out == test_out