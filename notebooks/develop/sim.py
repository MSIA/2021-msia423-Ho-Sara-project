from difflib import SequenceMatcher
from Levenshtein import distance

def sim_sm(a, b):
    return SequenceMatcher(None, a, b).ratio()

def lev_sim(a, b):
    return distance(None, a, b).ratio()
