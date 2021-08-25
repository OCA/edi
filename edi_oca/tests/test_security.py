# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo_test_helper import FakeModelLoader

from odoo.exceptions import AccessError, ValidationError

from .common import EDIBackendCommonTestCase


class TestEDIExchangeRecordSecurity(EDIBackendCommonTestCase):
    @classmethod
    def _setup_records(cls):
        super()._setup_records()
        # Load fake models ->/
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .fake_models import EdiExchangeConsumerTest

        cls.loader.update_registry((EdiExchangeConsumerTest,))

        cls.group = cls.env["res.groups"].create({"name": "Demo Group"})
        cls.ir_access = cls.env["ir.model.access"].create(
            {
                "name": "model access",
                "model_id": cls.env.ref("edi_oca.model_edi_exchange_consumer_test").id,
                "group_id": cls.group.id,
                "perm_read": True,
                "perm_write": True,
                "perm_create": True,
                "perm_unlink": True,
            }
        )
        cls.rule = cls.env["ir.rule"].create(
            {
                "name": "Exchange Record rule demo",
                "model_id": cls.env.ref("edi_oca.model_edi_exchange_consumer_test").id,
                "domain_force": "[('name', '=', 'test')]",
                "groups": [(4, cls.group.id)],
            }
        )
        cls.user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True, mail_notrack=True)
            .create(
                {
                    "name": "Poor Partner (not integrating one)",
                    "email": "poor.partner@ododo.com",
                    "login": "poorpartner",
                    "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
                }
            )
        )
        cls.consumer_record = cls.env["edi.exchange.consumer.test"].create(
            {"name": "test"}
        )
        cls.exchange_type_out.exchange_filename_pattern = "{record.id}"

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def create_record(self, user=False):
        vals = {
            "model": self.consumer_record._name,
            "res_id": self.consumer_record.id,
        }
        backend = self.backend
        if user:
            # backend = backend.with_user(user)
            backend = backend.sudo(user=user.id)
        return backend.create_record("test_csv_output", vals)

    def test_superuser_create(self):
        exchange_record = self.create_record()
        self.assertTrue(exchange_record)

    def test_group_create(self):
        self.user.write({"groups_id": [(4, self.group.id)]})
        exchange_record = self.create_record()
        self.assertTrue(exchange_record)

    def test_rule_no_create(self):
        self.user.write({"groups_id": [(4, self.group.id)]})
        self.consumer_record.name = "no_rule"
        with self.assertRaisesRegex(ValidationError, "Exchange Record rule demo"):
            self.create_record(self.user)

    def test_no_group_no_create(self):
        with self.assertRaisesRegex(
            ValidationError,
            "The requested operation cannot be completed due to security restrictions",
        ):
            self.create_record(self.user)

    def test_no_group_no_read(self):
        exchange_record = self.create_record()
        with self.assertRaisesRegex(
            AccessError, "Sorry, you are not allowed to access this document"
        ):
            exchange_record.sudo(user=self.user.id).read()

    def test_rule_no_read(self):
        exchange_record = self.create_record()
        self.user.write({"groups_id": [(4, self.group.id)]})
        self.assertTrue(exchange_record.sudo(user=self.user.id).read())
        self.consumer_record.name = "no_rule"
        with self.assertRaisesRegex(
            AccessError,
            "The requested operation cannot be completed due to security restrictions",
        ):
            exchange_record.sudo(user=self.user.id).read()

    def test_no_group_no_unlink(self):
        exchange_record = self.create_record()
        with self.assertRaisesRegex(
            AccessError, "Sorry, you are not allowed to modify this document."
        ):
            exchange_record.sudo(user=self.user.id).unlink()

    def test_group_unlink(self):
        exchange_record = self.create_record()
        self.user.write({"groups_id": [(4, self.group.id)]})
        self.assertTrue(exchange_record.sudo(user=self.user.id).unlink())

    def test_rule_no_unlink(self):
        exchange_record = self.create_record()
        self.user.write({"groups_id": [(4, self.group.id)]})
        self.consumer_record.name = "no_rule"
        with self.assertRaisesRegex(AccessError, "Exchange Record rule demo"):
            exchange_record.sudo(user=self.user.id).unlink()

    def test_no_group_no_search(self):
        exchange_record = self.create_record()
        self.assertEqual(
            0,
            self.env["edi.exchange.record"]
            .sudo(user=self.user.id)
            .search_count([("id", "=", exchange_record.id)]),
        )

    def test_group_search(self):
        exchange_record = self.create_record()
        self.user.write({"groups_id": [(4, self.group.id)]})
        self.assertEqual(
            1,
            self.env["edi.exchange.record"]
            .sudo(user=self.user.id)
            .search_count([("id", "=", exchange_record.id)]),
        )

    def test_rule_no_search(self):
        exchange_record = self.create_record()
        self.user.write({"groups_id": [(4, self.group.id)]})
        self.consumer_record.name = "no_rule"
        self.assertEqual(
            0,
            self.env["edi.exchange.record"]
            .sudo(user=self.user.id)
            .search_count([("id", "=", exchange_record.id)]),
        )

    def test_no_group_no_write(self):
        exchange_record = self.create_record()
        with self.assertRaisesRegex(
            AccessError, "Sorry, you are not allowed to modify this document"
        ):
            exchange_record.sudo(user=self.user.id).write(
                {"external_identifier": "1234"}
            )

    def test_group_write(self):
        exchange_record = self.create_record()
        self.user.write({"groups_id": [(4, self.group.id)]})
        exchange_record.sudo(user=self.user.id).write({"external_identifier": "1234"})
        self.assertEqual(exchange_record.external_identifier, "1234")

    def test_rule_no_write(self):
        exchange_record = self.create_record()
        self.user.write({"groups_id": [(4, self.group.id)]})
        self.consumer_record.name = "no_rule"
        with self.assertRaisesRegex(AccessError, "Exchange Record rule demo"):
            exchange_record.sudo(user=self.user.id).write(
                {"external_identifier": "1234"}
            )
