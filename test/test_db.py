import sys
import os
import pandas as pd
from numpy import array

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
from db import remove_accents, render_text, render_news_col


def test_remove_accents_ca():
    str_in = """Authentic mapo tofu is powerfully spicy with both
         conventional "heat" spiciness and the characteristic málà (numbing
         spiciness) flavor of Sichuan cuisine. The feel of the particular dish
         is often described by cooks using seven specific Chinese adjectives:
         má 麻 (numbing), là 辣 (spicy hot), tàng 烫 (hot temperature), xiān
         鲜 (fresh), nèn 嫩 (tender and soft), xiāng 香 (aromatic), and sū 酥 (flaky).
        """
    test_out = remove_accents(str_in)

    true_out = """Authentic mapo tofu is powerfully spicy with both
         conventional "heat" spiciness and the characteristic mala (numbing
         spiciness) flavor of Sichuan cuisine. The feel of the particular dish
         is often described by cooks using seven specific Chinese adjectives:
         ma Ma  (numbing), la La  (spicy hot), tang Tang  (hot temperature), xian
         Xian  (fresh), nen Nen  (tender and soft), xiang Xiang  (aromatic), and su Su  (flaky).
        """
    assert test_out == true_out


def test_remove_accents_es():
    str_in = """Iñárritu was born on 15 August 1963 in
         Mexico City, the youngest of seven siblings, to Luz María Iñárritu
         and Héctor González Gama. Héctor was a banker who owned a
         ranch, but went bankrupt when Iñárritu was five.
        """
    test_out = remove_accents(str_in)

    true_out = """Inarritu was born on 15 August 1963 in
         Mexico City, the youngest of seven siblings, to Luz Maria Inarritu
         and Hector Gonzalez Gama. Hector was a banker who owned a
         ranch, but went bankrupt when Inarritu was five.
        """
    assert test_out == true_out


def test_render_text():
    sample_string = """Bill Ackman's Pershing Square nears biggest-ever SPAC deal
        with Universal Music, source says - Billionaire investor Bill Ackman
        is nearing a $40 billion deal to take Universal Music public,
        the largest SPAC deal ever, a source said.
        """

    test_out = render_text(sample_string,
                           ['Bill Ackman', 'Pershing Square',
                            'Universal Music', 'Universal Music'])

    true_out = """<span class="highlight">Bill Ackman</span>\'s <span class="highlight">Pershing Square</span> nears biggest-ever SPAC deal
        with <span class="highlight"><span class="highlight">Universal Music</span></span>, source says - Billionaire investor <span class="highlight">Bill Ackman</span>
        is nearing a $40 billion deal to take <span class="highlight"><span class="highlight">Universal Music</span></span> public,
        the largest SPAC deal ever, a source said.
        """
    assert test_out == true_out


def test_render_news_col():

    args = {'raw_column': 'news',
            'new_column': 'news_dis',
            'entity_column': 'entity'}

    in_values = array([['Jun-05-2021', 2,
        "Max Kellerman on why he's intrigued by Floyd Mayweather vs. Logan Paul #Shorts - ESPN",
        'Max Kellerman'],
       ['Jun-05-2021', 2,
        "Max Kellerman on why he's intrigued by Floyd Mayweather vs. Logan Paul #Shorts - ESPN",
        'Shorts - ESPN (organization)'],
       ['Jun-05-2021', 3,
        "Nigeria Suspends Twitter After It Deleted A Tweet By The President -   Twitter deleted Muhammadu Buhari's post on Wednesday, calling it abusive, after the president threatened suspected separatist militants in the southeast.",
        'Suspends Twitter'],
       ['Jun-05-2021', 3,
        "Nigeria Suspends Twitter After It Deleted A Tweet By The President -   Twitter deleted Muhammadu Buhari's post on Wednesday, calling it abusive, after the president threatened suspected separatist militants in the southeast.",
        "Muhammadu Buhari's"],
       ['Jun-05-2021', 5,
        'Jennifer Lopez and Ben Affleck are leaving ‘no stone uncovered’ with rekindled romance: source -   "The Way Back" star and the "Hustlers" actress appear to be giving their love a second go-around.',
        'Jennifer Lopez']], dtype=object)

    in_columns = ['date', 'news_id', 'news', 'entity']

    df_in = pd.DataFrame(in_values, columns=in_columns)
    df_in['news_id'] = pd.to_numeric(df_in['news_id'])
    news_df_in = df_in[['date', 'news_id', 'news']].drop_duplicates()

    df_test = render_news_col(news_df_in, df_in, args)

    true_values = array([['Jun-05-2021', 2,
        "Max Kellerman on why he's intrigued by Floyd Mayweather vs. Logan Paul #Shorts - ESPN",
        '<span class="highlight">Max Kellerman</span> on why he\'s intrigued by Floyd Mayweather vs. Logan Paul #<span class="highlight">Shorts - ESPN</span>'],
       ['Jun-05-2021', 3,
        "Nigeria Suspends Twitter After It Deleted A Tweet By The President -   Twitter deleted Muhammadu Buhari's post on Wednesday, calling it abusive, after the president threatened suspected separatist militants in the southeast.",
        'Nigeria <span class="highlight">Suspends Twitter</span> After It Deleted A Tweet By The President -   Twitter deleted <span class="highlight">Muhammadu Buhari\'s</span> post on Wednesday, calling it abusive, after the president threatened suspected separatist militants in the southeast.'],
       ['Jun-05-2021', 5,
        'Jennifer Lopez and Ben Affleck are leaving ‘no stone uncovered’ with rekindled romance: source -   "The Way Back" star and the "Hustlers" actress appear to be giving their love a second go-around.',
        '<span class="highlight">Jennifer Lopez</span> and Ben Affleck are leaving ‘no stone uncovered’ with rekindled romance: source -   "The Way Back" star and the "Hustlers" actress appear to be giving their love a second go-around.']],
      dtype=object)

    true_columns = ['date', 'news_id', 'news', 'news_dis']
    true_index = pd.Int64Index([0, 2, 4], dtype='int64')
    df_true = pd.DataFrame(true_values, columns=true_columns, index=true_index)
    df_true['news_id'] = pd.to_numeric(df_true['news_id'])

    pd.testing.assert_frame_equal(df_test, df_true)
