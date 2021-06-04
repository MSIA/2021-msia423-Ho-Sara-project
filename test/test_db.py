import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")

from db import remove_accents, render_text


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
