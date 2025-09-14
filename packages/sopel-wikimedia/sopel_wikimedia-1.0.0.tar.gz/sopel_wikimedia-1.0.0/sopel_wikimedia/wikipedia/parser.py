import re
from html.parser import HTMLParser


class WikiParser(HTMLParser):
    NO_CONSUME_TAGS = ("sup", "style")
    """Tags whose contents should always be ignored.

    These are used in things like inline citations or section "hatnotes", none
    of which are useful output for IRC.
    """

    def __init__(self, section_name):
        HTMLParser.__init__(self)
        self.consume = True
        self.no_consume_depth = 0
        self.is_header = False
        self.section_name = section_name

        self.citations = False
        self.messagebox = False
        self.span_depth = 0
        self.div_depth = 0

        self.result = ""

    def handle_starttag(self, tag, attrs):
        if tag in self.NO_CONSUME_TAGS:
            self.consume = False
            self.no_consume_depth += 1

        elif re.match(r"^h\d$", tag):
            self.is_header = True

        elif tag == "span":
            if self.span_depth:
                self.span_depth += 1
            else:
                for attr in attrs:  # remove 'edit' tags, and keep track of depth for nested <span> tags
                    if attr[0] == "class" and "edit" in attr[1]:
                        self.span_depth += 1

        elif tag == "div":
            # We want to skip thumbnail text, the table of contents, and section "hatnotes".
            # This also requires tracking div nesting level.
            if self.div_depth:
                self.div_depth += 1
            else:
                for attr in attrs:
                    if attr[0] == "class" and (
                        "thumb" in attr[1]
                        or "hatnote" in attr[1]
                        or attr[1] == "toc"
                    ):
                        self.div_depth += 1
                        break

        elif tag == "table":
            # Message box templates are what we want to ignore here
            for attr in attrs:
                if attr[0] == "class" and any(
                    classname in attr[1].lower()
                    for classname in [
                        # Most of list from https://en.wikipedia.org/wiki/Template:Mbox_templates_see_also
                        "ambox",  # messageboxes on article pages
                        "cmbox",  # messageboxes on category pages
                        "imbox",  # messageboxes on file (image) pages
                        "tmbox",  # messageboxes on talk pages
                        "fmbox",  # header and footer messageboxes
                        "ombox",  # messageboxes on other types of page
                        "mbox",  # for messageboxes that are used in different namespaces
                                 # and change their presentation accordingly
                        "dmbox",  # for disambiguation messageboxes
                    ]
                ):
                    self.messagebox = True

        elif tag == "ol":
            for attr in attrs:
                if attr[0] == "class" and "references" in attr[1]:
                    self.citations = True  # once we hit citations, we can stop

    def handle_endtag(self, tag):
        if not self.consume and tag in self.NO_CONSUME_TAGS:
            if self.no_consume_depth:
                self.no_consume_depth -= 1
            if not self.no_consume_depth:
                self.consume = True
        if self.is_header and re.match(r"^h\d$", tag):
            self.is_header = False
        if self.span_depth and tag == "span":
            self.span_depth -= 1
        if self.div_depth and tag == "div":
            self.div_depth -= 1
        if self.messagebox and tag == "table":
            self.messagebox = False

    def handle_data(self, data):
        if self.consume and not any([self.citations, self.messagebox, self.span_depth, self.div_depth]):
            # Skip the initial header info only
            if not self.is_header and data == self.section_name:
                self.result += data

    def get_result(self):
        return self.result
