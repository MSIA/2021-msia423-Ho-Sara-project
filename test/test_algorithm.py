import sys
import os
import pandas as pd
from numpy import array

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
from algorithm import sim_score, remove_stopwords


def test_sim_score():
    in1 = """GMC just unveiled its $100,000 Hummer EV SUV with 830-horsepower
     that will hit streets in 2023 (GM). The Hummer EV pickup won't be the
     only "supertruck" in GMC's fleet after the automaker unveiled its Hummer
     EV SUV variant on Saturday. It's slated for release in spring 2023."""

    in2 = """"The GMC Hummer EV is both an upcoming off-road luxury electric
     vehicle produced by GMC (simply referred to as Hummer EV; and badged as
     HEV), and its own sub-brand. The Hummer EV line was launched in October
     2020 through a live stream.\nThe Hummer EV sub-brand includes a pickup
     truck (SUT) and a confirmed Sport Utility Vehicle (SUV) that was
     introduced on 3rd of April 2021."""

    test_out = round(sim_score([in1, in2]), 2)
    true_out = 0.11

    assert test_out == true_out


# def test_remove_stopwords():
#     print()
