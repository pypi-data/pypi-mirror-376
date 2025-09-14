import importlib.metadata

__version__ = importlib.metadata.version("sopel-wikimedia")


PLUGIN_USER_AGENT = "sopel-wikimedia/{version} (https://sopel.chat/)".format(
    version=__version__
)
WIKI_REQUEST_HEADERS = {
    "User-Agent": PLUGIN_USER_AGENT,
}
