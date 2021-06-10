import os
import sys
import pandas as pd
from numpy import array
from collections import Counter

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
from algorithm import join_data, text_to_vector, get_cosine, remove_stopwords


def test_join_data():
    news_in_values = [[0,
            'Sony announces WF-1000XM4 noise-canceling earbuds with LDAC and IPX4 water resistance -  The new WF-1000XM4 earbuds improve on Sony’s last noise-canceling earbuds with longer battery life, IPX4 water resistance, and even better sound with support for LDAC.'],
        [1,
            "Pelosi urges Democrats to continue voting rights push, despite Manchin -  After Manchin infuriated Democrats by saying he would not support the party's sweeping voting rights bill, the speaker implored the party not to shift focus."],
        [2,
            'Man Slaps Macron During Visit to Southern France - The  Two people were arrested after a man slapped the French president as he was approaching a small crowd, prompting condemnation of the attack across the political spectrum.'],
        [3,
            'Justice Department Continues Trump Defense In E. Jean Carroll Suit -  The Justice Department simultaneously distanced itself from the allegations Carroll has made that former President Donald Trump sexually assaulted her in the 1990s.'],
        [4,
            "Biogen faces tough questions over $56K-a-year price of newly approved Alzheimer's drug -  Biogen on Tuesday faced tough questions from Wall Street analysts over the $56,000 annual cost of its newly approved Alzheimer's drug, Aduhelm."]]
    news_in_columns = ['news_id', 'news']
    news_df_in = pd.DataFrame(news_in_values, columns = news_in_columns)
    wiki_in_values = [[0, 'Sony (organization)', 'Sony'],
        [0, 'WF-1000XM4', 'List of minor planets: 3001–4000'],
        [0, 'LDAC (organization)', 'Audio coding format'],
        [0, 'IPX4 (organization)', 'OSI model'],
        [1, 'Democrats', 'Democrat'],
        [1, 'Manchin -  ', 'Joe Manchin'],
        [2, 'French', 'French'],
        [3, 'Justice Department (organization)',
            'United States Department of Justice'],
        [3, 'Continues Trump', 'Donald Trump'],
        [3, 'Carroll (organization)', 'Bonnie Carroll']]
    wiki_in_columns = ['news_id', 'entity', 'title']
    wiki_df_in = pd.DataFrame(wiki_in_values, columns = wiki_in_columns)
    joined_in_values = [[0, 0, 'Sony (organization)', 'Sony',
            'Sony announces WF-1000XM4 noise-canceling earbuds with LDAC and IPX4 water resistance -  The new WF-1000XM4 earbuds improve on Sony’s last noise-canceling earbuds with longer battery life, IPX4 water resistance, and even better sound with support for LDAC.',
            'Jun-09-2021'],
        [1, 0, 'WF-1000XM4', 'List of minor planets: 3001–4000',
            'Sony announces WF-1000XM4 noise-canceling earbuds with LDAC and IPX4 water resistance -  The new WF-1000XM4 earbuds improve on Sony’s last noise-canceling earbuds with longer battery life, IPX4 water resistance, and even better sound with support for LDAC.',
            'Jun-09-2021'],
        [2, 0, 'LDAC (organization)', 'Audio coding format',
            'Sony announces WF-1000XM4 noise-canceling earbuds with LDAC and IPX4 water resistance -  The new WF-1000XM4 earbuds improve on Sony’s last noise-canceling earbuds with longer battery life, IPX4 water resistance, and even better sound with support for LDAC.',
            'Jun-09-2021'],
        [3, 0, 'IPX4 (organization)', 'OSI model',
            'Sony announces WF-1000XM4 noise-canceling earbuds with LDAC and IPX4 water resistance -  The new WF-1000XM4 earbuds improve on Sony’s last noise-canceling earbuds with longer battery life, IPX4 water resistance, and even better sound with support for LDAC.',
            'Jun-09-2021'],
        [4, 1, 'Democrats', 'Democrat',
            "Pelosi urges Democrats to continue voting rights push, despite Manchin -  After Manchin infuriated Democrats by saying he would not support the party's sweeping voting rights bill, the speaker implored the party not to shift focus.",
            'Jun-09-2021'],
        [5, 1, 'Manchin -  ', 'Joe Manchin',
            "Pelosi urges Democrats to continue voting rights push, despite Manchin -  After Manchin infuriated Democrats by saying he would not support the party's sweeping voting rights bill, the speaker implored the party not to shift focus.",
            'Jun-09-2021'],
        [6, 2, 'French', 'French',
            'Man Slaps Macron During Visit to Southern France - The  Two people were arrested after a man slapped the French president as he was approaching a small crowd, prompting condemnation of the attack across the political spectrum.',
            'Jun-09-2021'],
        [7, 3, 'Justice Department (organization)',
            'United States Department of Justice',
            'Justice Department Continues Trump Defense In E. Jean Carroll Suit -  The Justice Department simultaneously distanced itself from the allegations Carroll has made that former President Donald Trump sexually assaulted her in the 1990s.',
            'Jun-09-2021'],
        [8, 3, 'Continues Trump', 'Donald Trump',
            'Justice Department Continues Trump Defense In E. Jean Carroll Suit -  The Justice Department simultaneously distanced itself from the allegations Carroll has made that former President Donald Trump sexually assaulted her in the 1990s.',
            'Jun-09-2021'],
        [9, 3, 'Carroll (organization)', 'Bonnie Carroll',
            'Justice Department Continues Trump Defense In E. Jean Carroll Suit -  The Justice Department simultaneously distanced itself from the allegations Carroll has made that former President Donald Trump sexually assaulted her in the 1990s.',
            'Jun-09-2021']]
    joined_in_columns = ['wiki_id', 'news_id', 'entity', 'title', 'news', 'date']
    joined_df_true = pd.DataFrame(joined_in_values, columns = joined_in_columns)
    
    joined_df_test = join_data(news_df_in, wiki_df_in)
    pd.testing.assert_frame_equal(joined_df_test, joined_df_true)


def test_text_to_vector():
    in_text = """Prince Harry and Meghan Markle announce birth of new baby - Prince Harry and Meghan Markle announced the birth of their second child on Sunday. The baby's name, Lilibet"""

    test_out = text_to_vector(in_text)

    true_out = Counter({'Prince': 2, 'Harry': 2, 'and': 2, 'Meghan': 2,
        'Markle': 2, 'announce': 1, 'birth': 2,  'of': 2, 'new': 1,
        'baby': 2, 'announced': 1, 'the': 1, 'their': 1, 'second': 1,
        'child': 1, 'on': 1, 'Sunday': 1, 'The': 1, 's': 1, 'name': 1,
        'Lilibet': 1})

    assert test_out == true_out


def test_get_cosine():
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

    test_out = get_cosine([in1, in2])
    assert round(test_out, 5) == 0.40668


def test_remove_stopwords():
    news_in_values = [[0,
            'Sony announces WF-1000XM4 noise-canceling earbuds with LDAC and IPX4 water resistance -  The new WF-1000XM4 earbuds improve on Sony’s last noise-canceling earbuds with longer battery life, IPX4 water resistance, and even better sound with support for LDAC.'],
        [1,
            "Pelosi urges Democrats to continue voting rights push, despite Manchin -  After Manchin infuriated Democrats by saying he would not support the party's sweeping voting rights bill, the speaker implored the party not to shift focus."],
        [2,
            'Man Slaps Macron During Visit to Southern France - The  Two people were arrested after a man slapped the French president as he was approaching a small crowd, prompting condemnation of the attack across the political spectrum.'],
        [3,
            'Justice Department Continues Trump Defense In E. Jean Carroll Suit -  The Justice Department simultaneously distanced itself from the allegations Carroll has made that former President Donald Trump sexually assaulted her in the 1990s.'],
        [4,
            "Biogen faces tough questions over $56K-a-year price of newly approved Alzheimer's drug -  Biogen on Tuesday faced tough questions from Wall Street analysts over the $56,000 annual cost of its newly approved Alzheimer's drug, Aduhelm."]]
    news_in_columns = ['news_id', 'news']
    news_df_in = pd.DataFrame(news_in_values, columns = news_in_columns)

    true_values = [[0,
        'Sony announces WF-1000XM4 noise-canceling earbuds with LDAC and IPX4 water resistance -  The new WF-1000XM4 earbuds improve on Sony’s last noise-canceling earbuds with longer battery life, IPX4 water resistance, and even better sound with support for LDAC.',
        'sony announces wf-1000xm4 noise-canceling earbuds ldac ipx4 water resistance - new wf-1000xm4 earbuds improve sony’s last noise-canceling earbuds longer battery life, ipx4 water resistance, even better sound support ldac.'],
       [1,
        "Pelosi urges Democrats to continue voting rights push, despite Manchin -  After Manchin infuriated Democrats by saying he would not support the party's sweeping voting rights bill, the speaker implored the party not to shift focus.",
        "pelosi urges democrats continue voting rights push, despite manchin - manchin infuriated democrats saying would support party's sweeping voting rights bill, speaker implored party shift focus."],
       [2,
        'Man Slaps Macron During Visit to Southern France - The  Two people were arrested after a man slapped the French president as he was approaching a small crowd, prompting condemnation of the attack across the political spectrum.',
        'man slaps macron visit southern france - two people arrested man slapped french president approaching small crowd, prompting condemnation attack across political spectrum.'],
       [3,
        'Justice Department Continues Trump Defense In E. Jean Carroll Suit -  The Justice Department simultaneously distanced itself from the allegations Carroll has made that former President Donald Trump sexually assaulted her in the 1990s.',
        'justice department continues trump defense e. jean carroll suit - justice department simultaneously distanced allegations carroll made former president donald trump sexually assaulted 1990s.'],
       [4,
        "Biogen faces tough questions over $56K-a-year price of newly approved Alzheimer's drug -  Biogen on Tuesday faced tough questions from Wall Street analysts over the $56,000 annual cost of its newly approved Alzheimer's drug, Aduhelm.",
        "biogen faces tough questions $56k-a-year price newly approved alzheimer's drug - biogen tuesday faced tough questions wall street analysts $56,000 annual cost newly approved alzheimer's drug, aduhelm."]]
    
    true_columns = ['news_id', 'news', 'news_processed']
    true_out = pd.DataFrame(true_values, columns=true_columns)

    test_out = remove_stopwords(news_df_in, {'raw_features': ['news'], 'processed_features': ['news_processed']})

    pd.testing.assert_frame_equal(test_out, true_out)