# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import mock
from contextlib import contextmanager
from odoo.tests.common import tagged

from odoo.addons.component.tests.common import TransactionComponentCase


@tagged("-at_install", "post_install")
class CommonWebService(TransactionComponentCase):
    def _setup_context(self):
        return dict(
            self.env.context, tracking_disable=True, test_queue_job_no_delay=True,
        )

    def _setup_env(self):
        self.env = self.env(context=self._setup_context())

    def _setup_records(self):
        pass

    def setUp(self):
        super(CommonWebService, self).setUp()
        self._setup_env()
        self._setup_records()


@contextmanager
def mock_cursor(cr):
    with mock.patch("odoo.sql_db.Connection.cursor") as mocked_cursor_call:
        org_close = cr.close
        org_autocommit = cr.autocommit
        try:
            cr.close = mock.Mock()
            cr.autocommit = mock.Mock()
            cr.commit = mock.Mock()
            mocked_cursor_call.return_value = cr
            yield
        finally:
            cr.close = org_close
    cr.autocommit = org_autocommit
