# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class FakeComponentMixin(Component):

    FAKED_COLLECTOR = []

    def _fake_it(self):
        if self.env.context.get("test_break_it"):
            raise ValueError(self.env.context.get("test_break_it", "YOU BROKE IT!"))
        update_values = self.env.context.get("fake_update_values")
        if update_values:
            self.exchange_record.write(update_values)
        self.FAKED_COLLECTOR.append(self._call_key(self.exchange_record))
        return self.env.context.get("fake_output", self._call_key(self.exchange_record))

    @classmethod
    def _call_key(cls, rec):
        return "{}: {}".format(cls._name, rec.id)

    @classmethod
    def reset_faked(cls):
        cls.FAKED_COLLECTOR = []

    @classmethod
    def check_called_for(cls, rec):
        return cls._call_key(rec) in cls.FAKED_COLLECTOR

    @classmethod
    def check_not_called_for(cls, rec):
        return cls._call_key(rec) not in cls.FAKED_COLLECTOR


class FakeOutputGenerator(FakeComponentMixin):
    _name = "fake.output.generator"
    _inherit = "edi.component.output.mixin"
    _usage = "edi.output.generate.demo_backend.test_csv_output"

    def generate(self):
        return self._fake_it()


class FakeOutputSender(FakeComponentMixin):
    _name = "fake.output.sender"
    _inherit = "edi.component.send.mixin"
    _usage = "edi.output.send.demo_backend.test_csv_output"

    def send(self):
        return self._fake_it()


class FakeOutputChecker(FakeComponentMixin):
    _name = "fake.output.checker"
    _inherit = "edi.component.check.mixin"
    _usage = "edi.output.check.demo_backend.test_csv_output"

    def check(self):
        return self._fake_it()


class FakeInputProcess(FakeComponentMixin):
    _name = "fake.input.process"
    _inherit = "edi.component.input.mixin"
    _usage = "edi.input.process.demo_backend.test_csv_input"

    def process(self):
        return self._fake_it()


class FakeInputReceive(FakeComponentMixin):
    _name = "fake.input.receive"
    _inherit = "edi.component.input.mixin"
    _usage = "edi.input.receive.demo_backend.test_csv_input"

    def receive(self):
        return self._fake_it()
