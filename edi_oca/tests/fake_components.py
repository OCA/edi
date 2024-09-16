# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.component.core import Component


class FakeComponentMixin(Component):

    FAKED_COLLECTOR = []

    # only for testing
    _action = ""

    def _fake_it(self):
        self.FAKED_COLLECTOR.append(self._call_key(self.exchange_record))
        if self.env.context.get("test_break_" + self._action):
            exception = self.env.context.get(
                "test_break_" + self._action, "YOU BROKE IT!"
            )
            if not isinstance(exception, Exception):
                exception = ValueError(exception)
            raise exception
        update_values = self.env.context.get("fake_update_values")
        if update_values:
            self.exchange_record.write(update_values)
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
    _usage = "output.generate"
    _backend_type = "demo_backend"
    _exchange_type = "test_csv_output"

    _action = "generate"

    def generate(self):
        return self._fake_it()


class FakeOutputSender(FakeComponentMixin):
    _name = "fake.output.sender"
    _inherit = "edi.component.send.mixin"
    _usage = "output.send"
    _backend_type = "demo_backend"
    _exchange_type = "test_csv_output"

    _action = "send"

    def send(self):
        return self._fake_it()


class FakeOutputChecker(FakeComponentMixin):
    _name = "fake.output.checker"
    _inherit = "edi.component.check.mixin"
    _usage = "output.check"
    _backend_type = "demo_backend"
    _exchange_type = "test_csv_output"

    _action = "check"

    def check(self):
        return self._fake_it()


class FakeInputProcess(FakeComponentMixin):
    _name = "fake.input.process"
    _inherit = "edi.component.input.mixin"
    _usage = "input.process"
    _backend_type = "demo_backend"
    _exchange_type = "test_csv_input"

    _action = "process"

    def process(self):
        return self._fake_it()


class FakeInputReceive(FakeComponentMixin):
    _name = "fake.input.receive"
    _inherit = "edi.component.input.mixin"
    _usage = "input.receive"
    _backend_type = "demo_backend"
    _exchange_type = "test_csv_input"

    _action = "receive"

    def receive(self):
        return self._fake_it()


class FakeOutputValidate(FakeComponentMixin):
    _name = "fake.out.validate"
    _inherit = "edi.component.validate.mixin"
    _usage = "output.validate"
    _backend_type = "demo_backend"
    _exchange_type = "test_csv_output"

    _action = "validate"

    def validate(self, value=None):
        self._fake_it()
        return


class FakeInputValidate(FakeComponentMixin):
    _name = "fake.in.validate"
    _inherit = "edi.component.validate.mixin"
    _usage = "input.validate"
    _backend_type = "demo_backend"
    _exchange_type = "test_csv_input"

    _action = "validate"

    def validate(self, value=None):
        self._fake_it()
        return
    
class FakeConfigurationListener(FakeComponentMixin):
    _name = "fake.configuration.listener"
    _inherit = "base.event.listener"
    _apply_on = ["edi.exchange.consumer.test"]


    # TODO: Add tests for partner_ids

    def on_record_write(self, record, fields=None, **kwargs):
        trigger = "on_record_write"
        edi_configuration = self.env['edi.configuration']
        if kwargs.get("vals", False):
            for rec in record:
                confs = edi_configuration.edi_get_conf(trigger, model_name=rec._name)
                for conf in confs:
                    conf.edi_exec_snippet_do(rec, **kwargs)
        return True

    def on_record_create(self, record, fields=None, **kwargs):
        trigger = "on_record_create"
        edi_configuration = self.env['edi.configuration']
        backend_id = self.env.ref("edi_oca.demo_edi_backend")
        val_list = kwargs.get("vals", False)
        if val_list:
            for rec, vals in zip(record, val_list):
                kwargs["vals"] = {rec.id: vals}
                confs = edi_configuration.edi_get_conf(trigger, model_name=rec._name, backend=backend_id)
                print("Configuring: ", confs)
                for conf in confs:
                    conf.edi_exec_snippet_do(rec, **kwargs)
        return True
