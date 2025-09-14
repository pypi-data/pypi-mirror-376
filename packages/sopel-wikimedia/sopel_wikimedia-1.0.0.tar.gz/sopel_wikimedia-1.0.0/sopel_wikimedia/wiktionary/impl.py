from __future__ import annotations

import re
from typing import Dict, List, Optional

import requests
from sopel.tools import web

from sopel_wikimedia import WIKI_REQUEST_HEADERS

# From https://en.wiktionary.org/wiki/Wiktionary:Entry_layout#Part_of_speech
PARTS_OF_SPEECH = [
    # Parts of speech
    "Adjective",
    "Adverb",
    "Ambiposition",
    "Article",
    "Circumposition",
    "Classifier",
    "Conjunction",
    "Contraction",
    "Counter",
    "Determiner",
    "Ideophone",
    "Interjection",
    "Noun",
    "Numeral",
    "Participle",
    "Particle",
    "Postposition",
    "Preposition",
    "Pronoun",
    "Proper noun",
    "Verb",
    # Morphemes
    "Circumfix",
    "Combining form",
    "Infix",
    "Interfix",
    "Prefix",
    "Root",
    "Suffix",
    # Symbols and characters
    "Diacritical mark",
    "Letter",
    "Ligature",
    "Number",
    "Punctuation mark",
    "Syllable",
    "Symbol",
    # Phrases
    "Phrase",
    "Proverb",
    "Prepositional phrase",
    # Han characters and language-specific varieties
    "Han character",
    "Hanzi",
    "Kanji",
    "Hanja",
    # Other
    "Romanization",
]
PARTS_OF_SPEECH_LOWER = [pos.lower() for pos in PARTS_OF_SPEECH]

URI = "https://en.wiktionary.org/w/index.php?title=%s&printable=yes"
R_SUP = re.compile(r"<sup[^>]+>.+?</sup>")  # Superscripts that are references only, not ordinal indicators, etc...
R_TAG = re.compile(r"<[^>]+>")
R_UL = re.compile(r"(?ims)<ul>.*?</ul>")

Etymology = Optional[str]
Definitions = Dict[str, List[str]]


def text(html: str) -> str:
    text = R_SUP.sub("", html)  # Remove superscripts that are references from definition
    text = R_TAG.sub("", text).strip()
    text = text.replace("\n", " ")
    text = text.replace("\r", "")
    text = text.replace("(intransitive", "(intr.")
    text = text.replace("(transitive", "(trans.")
    text = web.decode(text)

    return text.strip()


def wikt(word: str) -> tuple[Etymology, Definitions]:
    """
    Retrieve the Wiktionary entry
    """
    response = requests.get(
        URI % web.quote(word),
        headers=WIKI_REQUEST_HEADERS,
    )
    response.raise_for_status()
    txt = response.text
    txt = R_UL.sub("", txt)

    mode = None
    etymology = None
    definitions = {}

    for line in txt.splitlines():
        is_new_mode = False
        if 'id="Etymology' in line:
            mode = "etymology"
            is_new_mode = True
        else:
            for pos in PARTS_OF_SPEECH:
                if 'id="{}"'.format(pos.replace(" ", "_")) in line:
                    mode = pos.lower()
                    is_new_mode = True
                    break

        if not is_new_mode:
            if (mode == "etymology") and ("<p>" in line):
                if etymology is not None:
                    # multi-line etymologies do exist (e.g. see "mayhem")
                    etymology += " " + text(line)
                else:
                    etymology = text(line)
            # 'id="' can occur in definition lines <li> when <sup> tag is used for references;
            # make sure those are not excluded (e.g. see "abecedarian").
            elif ('id="' in line) and ("<li>" not in line):
                mode = None
            elif (mode is not None) and ("<li>" in line):
                definitions.setdefault(mode, []).append(text(line))

        if "<hr" in line:
            break

    return etymology, definitions


def format_wikt(result: str, definitions: Definitions, number=2) -> str:
    for part in PARTS_OF_SPEECH_LOWER:
        if part in definitions:
            defs = definitions[part][:number]
            result += " — {}: ".format(part)
            n = ["%s. %s" % (i + 1, e.strip(" .")) for i, e in enumerate(defs)]
            result += ", ".join(n)

    return result.strip(" .,")
