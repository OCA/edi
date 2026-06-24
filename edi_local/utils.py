# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re


def is_numeric(value, partial_integer=8, partial_decimal=None):
    partial_integer = partial_integer if "-" not in value else partial_integer - 1
    if partial_decimal:
        regex = re.compile(
            rf"^-?\d{{1,{partial_integer}}}(?:\.\d{{{partial_decimal}}})?$"
        )
    else:
        regex = re.compile(rf"^-?\d{{1,{partial_integer}}}$")
    return regex.match(str(value))


def is_alphanumeric(value, allow_character=None):
    ex_regex = "^[A-Za-z0-9 ]+$"
    if allow_character:
        ex_regex = rf"^[A-Za-z0-9 {allow_character}]+$"
    regex = re.compile(ex_regex)
    return regex.match(str(value))


def is_date(value):
    regex = re.compile(r"^\d{4}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])$")
    return regex.match(str(value))


def get_notification(
    message, tag="display_notification", type_message="info", sticky=False
):
    return {
        "type": "ir.actions.client",
        "tag": tag,
        "params": {
            "type": type_message,
            "sticky": sticky,
            "message": message,
            "next": {
                "type": "ir.actions.client",
                "tag": "soft_reload",
            },
        },
    }
