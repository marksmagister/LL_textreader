"""French verb tense from the form itself.

The tagger is unreliable here (8/16 on common forms, and it never produces a
conditional). These rules decide what the ending decides, and stay quiet
otherwise — a learner told that a conditional is a present is worse off than one
told nothing (CLAUDE.md rule 7). No model needed: these are pure functions.
"""

import pytest

from ll_textreader.nlp.languages.fr import refine_morph, tense_from_form

FINITE = "Mood=Ind|Number=Sing|Person=1|Tense=Pres|VerbForm=Fin"


@pytest.mark.parametrize(
    "surface,lemma,expected",
    [
        # built on the infinitive stem -> future or conditional, with certainty
        ("chanterais", "chanter", ("Cnd", "Pres")),
        ("chanterait", "chanter", ("Cnd", "Pres")),
        ("prendrions", "prendre", ("Cnd", "Pres")),
        ("chanterai", "chanter", ("Ind", "Fut")),
        ("marcherons", "marcher", ("Ind", "Fut")),
        ("finiront", "finir", ("Ind", "Fut")),
        # not on the infinitive stem, -ais/-ait/-aient -> imperfect
        ("chantais", "chanter", ("Ind", "Imp")),
        ("marchait", "marcher", ("Ind", "Imp")),
        ("avais", "avoir", ("Ind", "Imp")),
        # an irregular conditional also ends -rais, so the ending alone can't say
        ("serais", "être", None),
        ("aurait", "avoir", None),
        # a stem ending in r makes -rais ambiguous; stay quiet rather than guess
        ("montrais", "montrer", None),
        # -ions/-iez off the infinitive stem is also present subjunctive
        ("étions", "être", None),
        ("chante", "chanter", None),
    ],
)
def test_tense_from_form(surface, lemma, expected):
    assert tense_from_form(surface, lemma) == expected


def test_refine_corrects_the_tagger():
    """The tagger calls chanterais a present indicative; the ending says otherwise."""
    out = refine_morph("chanterais", "chanter", FINITE)
    assert "Mood=Cnd" in out and "Tense=Pres" in out
    assert "Person=1" in out  # person and number are the tagger's, and are fine


def test_refine_drops_an_untrustworthy_tense_rather_than_showing_it():
    """serions is a conditional. The tagger says present and the rules can't tell,
    so nothing is claimed about tense."""
    out = refine_morph("serions", "être", "Mood=Ind|Number=Plur|Person=1|Tense=Pres|VerbForm=Fin")
    assert "Mood=" not in out and "Tense=" not in out
    assert "Number=Plur" in out and "Person=1" in out


def test_refine_keeps_a_present_the_ending_cannot_contest():
    out = refine_morph("chante", "chanter", "Mood=Ind|Number=Sing|Person=1|Tense=Pres|VerbForm=Fin")
    assert "Mood=Ind" in out and "Tense=Pres" in out


def test_refine_keeps_futures_the_tagger_got_right():
    """viendront is irregular, so the rules are silent — but Fut is not the
    tagger's failure mode, so it is kept."""
    out = refine_morph("viendront", "venir", "Mood=Ind|Number=Plur|Person=3|Tense=Fut|VerbForm=Fin")
    assert "Tense=Fut" in out


def test_refine_leaves_participles_and_non_verbs_alone():
    part = "Gender=Masc|Number=Sing|Tense=Past|VerbForm=Part"
    assert refine_morph("mangé", "manger", part) == part
    noun = "Gender=Fem|Number=Plur"
    assert refine_morph("maisons", "maison", noun) == noun
    assert refine_morph("le", "le", "") == ""
