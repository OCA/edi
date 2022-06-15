# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import http


class CTRLFake(http.Controller):
    # Shortcut for dotted path
    _path = "odoo.addons.endpoint_route_handler.tests.fake_controllers.CTRLFake"

    def handler1(self, arg1, arg2=2):
        return arg1, arg2

    def handler2(self, arg1, arg2=2):
        return arg1, arg2

    def custom_handler(self, custom=None):
        return f"Got: {custom}"


class TestController(http.Controller):
    _path = "odoo.addons.endpoint_route_handler.tests.fake_controllers.TestController"

    def _do_something1(self, foo=None):
        return f"Got: {foo}"

    def _do_something2(self, default_arg, foo=None):
        return f"{default_arg} -> got: {foo}"
