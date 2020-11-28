# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class FakeOutputGenerator(Component):
    _name = "fake.output.generator"
    _inherit = "edi.component.output.mixin"
    _usage = "edi.output.demo_backend.test_csv_output"

    def generate(self):
        if self.env.context.get("test_break_it"):
            raise ValueError(self.env.context.get("test_break_it", "YOU BROKE IT!"))
        return self.env.context.get(
            "fake_output", "FAKE_OUTPUT: %d" % self.exchange_record.id
        )


class FakeOutputSender(Component):
    _name = "fake.output.sender"
    _inherit = "edi.component.send.mixin"
    _usage = "edi.send.demo_backend.test_csv_output"

    FAKE_SEND_COLLECTOR = []

    def send(self):
        if self.env.context.get("test_break_it"):
            raise ValueError(self.env.context.get("test_break_it", "YOU BROKE IT!"))
        self.FAKE_SEND_COLLECTOR.append(self.exchange_record._get_file_content())
        return self.env.context.get(
            "fake_output", "FAKE_OUTPUT: %d" % self.exchange_record.id
        )


class FakeOutputChecker(Component):
    _name = "fake.output.checker"
    _inherit = "edi.component.check.mixin"
    _usage = "edi.check.demo_backend.test_csv_output"

    def check(self):
        if self.env.context.get("test_break_it"):
            raise ValueError(self.env.context.get("test_break_it", "YOU BROKE IT!"))
        update_values = self.env.context.get("test_output_check_update_values")
        if update_values:
            self.exchange_record.write(update_values)
        return True
