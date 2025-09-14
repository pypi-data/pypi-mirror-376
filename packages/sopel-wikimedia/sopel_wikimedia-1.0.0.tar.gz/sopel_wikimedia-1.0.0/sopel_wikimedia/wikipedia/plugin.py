"""
wikipedia.py - Sopel Wikipedia Plugin
Copyright 2013 Elsie Powell - embolalia.com
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""

from __future__ import annotations

import logging
import re
from urllib.parse import quote, unquote, urlparse

from sopel import plugin

from .config import WikipediaSection
from .wiki import mw_image_description, mw_search, mw_section, mw_snippet

LOGGER = logging.getLogger(__name__)

PLUGIN_OUTPUT_PREFIX = "[wikipedia] "


def setup(bot):
    bot.config.define_section("wikipedia", WikipediaSection)


def configure(config):
    config.define_section("wikipedia", WikipediaSection)
    config.wikipedia.configure_setting(
        "default_lang", "Enter the default language to find articles from."
    )


# Matches a Wikipedia link (excluding /File: pages)
@plugin.url(r"https?:\/\/([a-z]+(?:\.m)?\.wikipedia\.org)\/wiki\/((?!File\:)[^ ]+)")
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def mw_info(bot, trigger, match=None):
    """Retrieves and outputs a snippet of the linked page."""
    server = match.group(1)
    page_info = urlparse(match.group(0))
    # in Python 3.9+ this can be str.removeprefix() instead, but we're confident that
    # "/wiki/" is at the start of the path anyway since it's part of the pattern
    trim_offset = len("/wiki/")
    article = unquote(page_info.path)[trim_offset:]
    section = unquote(page_info.fragment)

    if article.startswith("Special:"):
        # The MediaWiki query API does not include pages in the Special:
        # namespace, so there's no point bothering when we know this will error
        LOGGER.debug("Ignoring page in Special: namespace")
        return False

    if section:
        if section.startswith("cite_note-"):
            # Don't bother trying to retrieve a section snippet if cite-note is linked
            say_snippet(bot, trigger, server, article, show_url=False)
        elif section.startswith("/media"):
            # gh2316: media fragments are usually images; try to get an image description
            image = section[
                7:
            ]  # strip '/media' prefix in pre-3.9 friendly way
            say_image_description(bot, trigger, server, image)
        else:
            say_section(bot, trigger, server, article, section)
    else:
        say_snippet(bot, trigger, server, article, show_url=False)


@plugin.command("wikipedia", "wp")
@plugin.example(".wp San Francisco")
@plugin.output_prefix("[wikipedia] ")
def wikipedia(bot, trigger):
    """Search Wikipedia."""
    if trigger.group(2) is None:
        bot.reply("What do you want me to look up?")
        return plugin.NOLIMIT

    lang = choose_lang(bot, trigger)
    query = trigger.group(2)
    args = re.search(r"^-([a-z]{2,12})\s(.*)", query)
    if args is not None:
        lang = args.group(1)
        query = args.group(2)

    if not query:
        bot.reply("What do you want me to look up?")
        return plugin.NOLIMIT

    if query.startswith("Special:"):
        bot.reply(
            "Sorry, the MediaWiki API doesn't support querying the Special: namespace."
        )
        return False

    server = lang + ".wikipedia.org"
    query = mw_search(server, query, 1)
    if not query:
        bot.reply("I can't find any results for that.")
        return plugin.NOLIMIT
    else:
        query = query[0]
    say_snippet(bot, trigger, server, query, commanded=True)


@plugin.command("wplang")
@plugin.example(".wplang pl")
def wplang(bot, trigger):
    if not trigger.group(3):
        bot.reply(
            "Your current Wikipedia language is: {}".format(
                bot.db.get_nick_value(
                    trigger.nick,
                    "wikipedia_lang",
                    bot.config.wikipedia.default_lang,
                )
            )
        )
        return

    bot.db.set_nick_value(trigger.nick, "wikipedia_lang", trigger.group(3))
    bot.reply("Set your Wikipedia language to: {}".format(trigger.group(3)))


@plugin.command("wpclang")
@plugin.example(".wpclang ja")
@plugin.require_chanmsg()
@plugin.output_prefix(PLUGIN_OUTPUT_PREFIX)
def wpclang(bot, trigger):
    priv = bot.channels[trigger.sender.lower()].privileges[trigger.nick.lower()]
    if not (trigger.admin or priv >= plugin.OP):
        bot.reply(
            "You don't have permission to change this channel's Wikipedia language setting."
        )
        return plugin.NOLIMIT

    if not trigger.group(3):
        bot.say(
            "{}'s current Wikipedia language is: {}".format(
                trigger.sender,
                bot.db.get_nick_value(
                    trigger.nick,
                    "wikipedia_lang",
                    bot.config.wikipedia.default_lang,
                ),
            )
        )
        return

    bot.db.set_channel_value(
        trigger.sender, "wikipedia_lang", trigger.group(3)
    )
    bot.say(
        "Set {}'s Wikipedia language to: {}".format(
            trigger.sender, trigger.group(3)
        )
    )


def choose_lang(bot, trigger):
    """Determine what language to use for queries based on sender/context."""
    user_lang = bot.db.get_nick_value(trigger.nick, "wikipedia_lang")
    if user_lang:
        return user_lang

    if not trigger.sender.is_nick():
        channel_lang = bot.db.get_channel_value(
            trigger.sender, "wikipedia_lang"
        )
        if channel_lang:
            return channel_lang

    return bot.config.wikipedia.default_lang


def say_snippet(bot, trigger, server, query, show_url=True, commanded=False):
    page_name = query.replace("_", " ")
    query = quote(query.replace(" ", "_"))
    url = "https://{}/wiki/{}".format(server, query)

    # If the trigger looks like another instance of this plugin, assume it is
    if trigger.startswith(PLUGIN_OUTPUT_PREFIX) and trigger.endswith(
        " | " + url
    ):
        return

    try:
        snippet = mw_snippet(server, query)
        # Coalesce repeated whitespace to avoid problems with <math> on MediaWiki
        # see https://github.com/sopel-irc/sopel/issues/2259
        snippet = re.sub(r"\s+", " ", snippet)
    except KeyError:
        msg = 'Error fetching snippet for "{}".'.format(page_name)
        if commanded:
            bot.reply(msg)
        else:
            bot.say(msg)
        return

    msg = '{} | "{}'.format(page_name, snippet)

    trailing = '"'
    if show_url:
        trailing += " | " + url

    bot.say(msg, truncation=" […]", trailing=trailing)


def say_section(bot, trigger, server, query, section):
    page_name = query.replace("_", " ")
    query = quote(query.replace(" ", "_"))

    snippet = mw_section(server, query, section)
    if not snippet:
        bot.say(
            'Error fetching section "{}" for page "{}".'.format(
                section, page_name
            )
        )
        return

    msg = '{} - {} | "{}"'.format(
        page_name, section.replace("_", " "), snippet
    )
    bot.say(msg, truncation=' […]"')


def say_image_description(bot, trigger, server, image):
    desc = mw_image_description(server, image)

    if desc:
        bot.say(desc, truncation=" […]")
