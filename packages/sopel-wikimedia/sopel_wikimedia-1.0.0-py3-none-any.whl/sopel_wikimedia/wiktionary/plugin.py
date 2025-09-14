"""
wiktionary - Sopel Wiktionary Plugin
Copyright 2009, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""

from __future__ import annotations

from sopel import plugin

from .impl import format_wikt, wikt

PLUGIN_OUTPUT_PREFIX = "[wiktionary] "


@plugin.command("wt", "define", "dict")
@plugin.example(".wt bailiwick", "bailiwick — noun: 1. The district within which a bailie or bailiff has jurisdiction, 2. A person's concern or sphere of operations, their area of skill or authority")  # noqa
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def wiktionary(bot, trigger):
    """Look up a word on Wiktionary."""
    word = trigger.group(2)
    if word is None:
        bot.reply("You must tell me what to look up!")
        return

    _etymology, definitions = wikt(word)
    if not definitions:
        # Cast word to lower to check in case of mismatched user input
        _etymology, definitions = wikt(word.lower())
        if not definitions:
            bot.reply("Couldn't get any definitions for %s." % word)
            return

    result = format_wikt(word, definitions)
    if len(result) < 300:
        result = format_wikt(word, definitions, 3)
    if len(result) < 300:
        result = format_wikt(word, definitions, 5)

    bot.say(result, truncation=" […]")


@plugin.command("ety")
@plugin.example(".ety bailiwick", "bailiwick: From bailie (“bailiff”) and wick (“dwelling”), from Old English wīc.")
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def wiktionary_ety(bot, trigger):
    """Look up a word's etymology on Wiktionary."""
    word = trigger.group(2)
    if word is None:
        bot.reply("You must give me a word!")
        return

    etymology, _definitions = wikt(word)
    if not etymology:
        bot.reply("Couldn't get the etymology for %s." % word)
        return

    result = "{}: {}".format(word, etymology)

    bot.say(result, truncation=" […]")
