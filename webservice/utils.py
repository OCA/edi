# Copyright 2023 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def sanitize_url_for_log(url, blacklisted_keys=None):
    """Sanitize url to avoid loggin sensitive data"""
    blacklisted_keys = blacklisted_keys or ("apikey", "password", "pwd")
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=False)
    clean_query = {}

    def is_blacklisted(k):
        for bl_key in blacklisted_keys:
            if bl_key.lower() in k.lower():
                return True

    for k, v in query.items():
        if not is_blacklisted(k):
            clean_query[k] = v

    parsed = parsed._replace(query=urlencode(clean_query, True))
    return urlunparse(parsed)
