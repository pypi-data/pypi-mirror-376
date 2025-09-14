"""Configuration section for plugin."""

from __future__ import annotations

from sopel.config import types


class WikipediaSection(types.StaticSection):
    default_lang = types.ValidatedAttribute("default_lang", default="en")
    """The default language to find articles from (same as Wikipedia language subdomain)."""
