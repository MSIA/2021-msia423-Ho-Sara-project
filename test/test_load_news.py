import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
from load_news import create_id_col, remove_stopwords


def test_create_id_col():
    in_values = [['Sony announces WF-1000XM4 noise-canceling earbuds with LDAC and IPX4 water resistance -  The new WF-1000XM4 earbuds improve on Sony’s last noise-canceling earbuds with longer battery life, IPX4 water resistance, and even better sound with support for LDAC.'],
       ["Pelosi urges Democrats to continue voting rights push, despite Manchin -  After Manchin infuriated Democrats by saying he would not support the party's sweeping voting rights bill, the speaker implored the party not to shift focus."],
       ['Man Slaps Macron During Visit to Southern France - The  Two people were arrested after a man slapped the French president as he was approaching a small crowd, prompting condemnation of the attack across the political spectrum.'],
       ['Justice Department Continues Trump Defense In E. Jean Carroll Suit -  The Justice Department simultaneously distanced itself from the allegations Carroll has made that former President Donald Trump sexually assaulted her in the 1990s.'],
       ["Biogen faces tough questions over $56K-a-year price of newly approved Alzheimer's drug -  Biogen on Tuesday faced tough questions from Wall Street analysts over the $56,000 annual cost of its newly approved Alzheimer's drug, Aduhelm."],
       ["Capitol Police 'was aware of the potential for violence' and other takeaways from the Senate report on January 6 security failures -   Two Senate committees on Tuesday released the most comprehensive government report on the security failures leading up to the US Capitol insurrection on January 6, revealing new details about unheeded warnings, critical miscommunications and intelligence shor…"],
       ['Job openings spike to record 9.3M as businesses scramble to hire workers -  U.S. job openings hit a record high in April as employers scrambled to find workers amid the reopening of the economy.'],
       ["Stephen A. roasts Giannis and the Bucks, calls Game 2 a 'national embarrassment' | First Take - "],
       ["Khloé Kardashian calls Kanye West her 'brother for life' amid Kim divorce -  Khloé Kardashian gave fans plenty to keep up with in her latest post wishing Kanye West a happy birthday."],
       ['Best Moments From Clippers vs Jazz Season Series! - NBA']]
    in_columns = ['news']
    df_in = pd.DataFrame(in_values, columns=in_columns)
    test_out = create_id_col(df_in, 'news_id')

    out_values = [[0,
        'Sony announces WF-1000XM4 noise-canceling earbuds with LDAC and IPX4 water resistance -  The new WF-1000XM4 earbuds improve on Sony’s last noise-canceling earbuds with longer battery life, IPX4 water resistance, and even better sound with support for LDAC.'],
       [1,
        "Pelosi urges Democrats to continue voting rights push, despite Manchin -  After Manchin infuriated Democrats by saying he would not support the party's sweeping voting rights bill, the speaker implored the party not to shift focus."],
       [2,
        'Man Slaps Macron During Visit to Southern France - The  Two people were arrested after a man slapped the French president as he was approaching a small crowd, prompting condemnation of the attack across the political spectrum.'],
       [3,
        'Justice Department Continues Trump Defense In E. Jean Carroll Suit -  The Justice Department simultaneously distanced itself from the allegations Carroll has made that former President Donald Trump sexually assaulted her in the 1990s.'],
       [4,
        "Biogen faces tough questions over $56K-a-year price of newly approved Alzheimer's drug -  Biogen on Tuesday faced tough questions from Wall Street analysts over the $56,000 annual cost of its newly approved Alzheimer's drug, Aduhelm."],
       [5,
        "Capitol Police 'was aware of the potential for violence' and other takeaways from the Senate report on January 6 security failures -   Two Senate committees on Tuesday released the most comprehensive government report on the security failures leading up to the US Capitol insurrection on January 6, revealing new details about unheeded warnings, critical miscommunications and intelligence shor…"],
       [6,
        'Job openings spike to record 9.3M as businesses scramble to hire workers -  U.S. job openings hit a record high in April as employers scrambled to find workers amid the reopening of the economy.'],
       [7,
        "Stephen A. roasts Giannis and the Bucks, calls Game 2 a 'national embarrassment' | First Take - "],
       [8,
        "Khloé Kardashian calls Kanye West her 'brother for life' amid Kim divorce -  Khloé Kardashian gave fans plenty to keep up with in her latest post wishing Kanye West a happy birthday."],
       [9, 'Best Moments From Clippers vs Jazz Season Series! - NBA']]
    out_columns = ['news_id', 'news']
    true_out = pd.DataFrame(out_values, columns = out_columns)
    
    pd.testing.assert_frame_equal(test_out, true_out)

