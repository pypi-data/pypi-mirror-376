import logging
from urllib.parse import quote

import requests

from sopel_wikimedia import WIKI_REQUEST_HEADERS
from .parser import WikiParser

LOGGER = logging.getLogger(__name__)


def mw_image_description(server, image):
    """Retrieves the description for the given image."""
    params = "&".join(
        [
            "action=query",
            "prop=imageinfo",
            "format=json",
            "indexpageids=1",
            "iiprop=extmetadata",
            "iiextmetadatafilter=ImageDescription",
            "iilimit=1",
            "titles={image}".format(image=image),
        ]
    )
    url = "https://{server}/w/api.php?{params}".format(
        server=server, params=params
    )

    response = requests.get(url, headers=WIKI_REQUEST_HEADERS)
    json = response.json()

    try:
        query_data = json["query"]
        pageids = query_data["pageids"]
        pages = query_data["pages"]

        page = pages[pageids[0]]

        raw_desc = page["imageinfo"][0]["extmetadata"]["ImageDescription"][
            "value"
        ]

    except LookupError:
        LOGGER.exception(
            "Error getting image description for %r, response was: %r",
            image,
            json,
        )
        return None

    # Some descriptions contain markup, use WikiParser to discard that
    parser = WikiParser(image)
    parser.feed(raw_desc)
    desc = parser.get_result()
    desc = " ".join(desc.split())  # collapse multiple whitespace chars

    return desc


def mw_search(server, query, num):
    """Search a MediaWiki site

    Searches the specified MediaWiki server for the given query, and returns
    the specified number of results.
    """
    search_url = (
        "https://%s/w/api.php?format=json&action=query"
        "&list=search&srlimit=%d&srprop=timestamp&srwhat=text"
        "&srsearch="
    ) % (server, num)
    search_url += query
    query = requests.get(search_url, headers=WIKI_REQUEST_HEADERS).json()
    if "query" in query:
        query = query["query"]["search"]
        return [r["title"] for r in query]
    return None


def mw_snippet(server, query):
    """Retrieves a snippet of the given page from the given MediaWiki server."""
    snippet_url = (
        "https://" + server + "/w/api.php?format=json"
        "&action=query&prop=extracts&exintro&explaintext"
        "&exchars=500&redirects&titles="
    )
    snippet_url += query
    snippet = requests.get(snippet_url, headers=WIKI_REQUEST_HEADERS).json()
    snippet = snippet["query"]["pages"]

    # For some reason, the API gives the page *number* as the key, so we just
    # grab the first page number in the results.
    snippet = snippet[list(snippet.keys())[0]]

    return snippet["extract"]


def mw_section(server, query, section):
    """
    Retrieves a snippet from the specified section from the given page
    on the given server.
    """
    sections_url = (
        "https://{0}/w/api.php?format=json&redirects"
        "&action=parse&prop=sections&page={1}".format(server, query)
    )
    sections = requests.get(sections_url, headers=WIKI_REQUEST_HEADERS).json()

    fetch_title = section_number = None

    for entry in sections["parse"]["sections"]:
        if entry["anchor"] == section:
            section_number = entry["index"]
            # Needed to handle sections from transcluded pages properly
            # e.g. template documentation (usually pulled in from /doc subpage).
            # One might expect this prop to be nullable because in most cases it
            # will simply repeat the requested page title, but it's always set.
            fetch_title = entry.get("fromtitle")
            break

    if section_number is None or fetch_title is None:
        return None

    snippet_url = (
        "https://{0}/w/api.php?format=json&redirects"
        "&action=parse&page={1}&prop=text"
        "&section={2}"
    ).format(server, quote(fetch_title), section_number)

    data = requests.get(snippet_url, headers=WIKI_REQUEST_HEADERS).json()

    parser = WikiParser(section.replace("_", " "))
    parser.feed(data["parse"]["text"]["*"])
    text = parser.get_result()
    text = " ".join(text.split())  # collapse multiple whitespace chars

    return text
