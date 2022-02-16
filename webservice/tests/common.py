# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import tagged

from odoo.addons.component.tests.common import TransactionComponentCase


@tagged("-at_install", "post_install")
class CommonWebService(TransactionComponentCase):
    @classmethod
    def _setup_context(cls):
        return dict(
            cls.env.context, tracking_disable=True, test_queue_job_no_delay=True
        )

    @classmethod
    def _setup_env(cls):
        cls.env = cls.env(context=cls._setup_context())

    @classmethod
    def _setup_records(cls):
        pass

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_env()
        cls._setup_records()
