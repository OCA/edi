# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo_test_helper import FakeModelLoader

from odoo.exceptions import AccessError
from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import EDIBackendCommonTestCase


@tagged("at_install", "-post_install")
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
                    "groups_id": [(6, 0, [cls.env.ref("base_edi.group_edi_user").id])],
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
            backend = backend.with_user(user)
        return backend.create_record("test_csv_output", vals)

    def test_superuser_create(self):
        exchange_record = self.create_record()
        self.assertTrue(exchange_record)

    def test_group_create(self):
        self.user.write({"groups_id": [(4, self.group.id)]})
        exchange_record = self.create_record()
        self.assertTrue(exchange_record)

    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_rule_no_create(self):
        self.user.write({"groups_id": [(4, self.group.id)]})
        self.consumer_record.name = "no_rule"
        model = self.consumer_record
        msg = rf"not allowed to modify '{model._description}' \({model._name}\)"
        with self.assertRaisesRegex(AccessError, msg):
            self.create_record(self.user)

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_no_group_no_create(self):
        with self.assertRaisesRegex(AccessError, "You are not allowed to modify"):
            self.create_record(self.user)

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_no_group_no_read(self):
        exchange_record = self.create_record()
        model = self.consumer_record
        msg = rf"not allowed to access '{model._description}' \({model._name}\)"
        with self.assertRaisesRegex(AccessError, msg):
            exchange_record.with_user(self.user).read()

    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_rule_no_read(self):
        exchange_record = self.create_record()
        self.user.write({"groups_id": [(4, self.group.id)]})
        self.assertTrue(exchange_record.with_user(self.user).read())
        self.consumer_record.name = "no_rule"
        model = self.consumer_record
        msg = rf"not allowed to access '{model._description}' \({model._name}\)"
        with self.assertRaisesRegex(AccessError, msg):
            exchange_record.with_user(self.user).read()

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_no_group_no_unlink(self):
        exchange_record = self.create_record()
        with self.assertRaisesRegex(AccessError, "You are not allowed to modify"):
            exchange_record.with_user(self.user).unlink()

    @mute_logger("odoo.models.unlink")
    def test_group_unlink(self):
        exchange_record = self.create_record()
        self.user.write({"groups_id": [(4, self.group.id)]})
        self.assertTrue(exchange_record.with_user(self.user).unlink())

    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_rule_no_unlink(self):
        exchange_record = self.create_record()
        self.user.write({"groups_id": [(4, self.group.id)]})
        self.consumer_record.name = "no_rule"
        model = self.consumer_record
        msg = rf"not allowed to modify '{model._description}' \({model._name}\)"
        with self.assertRaisesRegex(AccessError, msg):
            exchange_record.with_user(self.user).unlink()

    def test_no_group_no_search(self):
        exchange_record = self.create_record()
        self.assertEqual(
            0,
            self.env["edi.exchange.record"]
            .with_user(self.user)
            .search_count([("id", "=", exchange_record.id)]),
        )

    def test_group_search(self):
        exchange_record = self.create_record()
        self.user.write({"groups_id": [(4, self.group.id)]})
        self.assertEqual(
            1,
            self.env["edi.exchange.record"]
            .with_user(self.user)
            .search_count([("id", "=", exchange_record.id)]),
        )

    def test_rule_no_search(self):
        exchange_record = self.create_record()
        self.user.write({"groups_id": [(4, self.group.id)]})
        self.consumer_record.name = "no_rule"
        self.assertEqual(
            0,
            self.env["edi.exchange.record"]
            .with_user(self.user)
            .search_count([("id", "=", exchange_record.id)]),
        )

    def test_search_no_record(self):
        # Consumer record no longer exists:
        #  exchange_record is hidden in search
        exchange_record = self.create_record()
        exchange_record.res_id = -1
        self.user.write({"groups_id": [(4, self.group.id)]})
        logger_name = "odoo.addons.edi_oca.models.edi_exchange_record"
        expected_msg = (
            f"WARNING:{logger_name}:"
            f"Deleted record {exchange_record.model},{exchange_record.res_id} "
            f"is referenced by edi.exchange.record [{exchange_record.id}]"
        )
        with self.assertLogs(logger_name, "WARNING") as watcher:
            self.assertEqual(
                0,
                self.env["edi.exchange.record"]
                .with_user(self.user)
                .search_count([("id", "=", exchange_record.id)]),
            )
            self.assertEqual(watcher.output, [expected_msg])

    def test_search_no_record_admin(self):
        # Consumer record no longer exists:
        #  user with group "Settings" has access
        exchange_record = self.create_record()
        exchange_record.res_id = -1
        admin_group = self.env.ref("base.group_system")
        self.user.write({"groups_id": [(4, self.group.id), (4, admin_group.id)]})
        self.assertEqual(
            1,
            self.env["edi.exchange.record"]
            .with_user(self.user)
            .search_count([("id", "=", exchange_record.id)]),
        )

    @mute_logger("odoo.addons.base.models.ir_model")
    def test_no_group_no_write(self):
        exchange_record = self.create_record()
        with self.assertRaisesRegex(AccessError, "You are not allowed to modify"):
            exchange_record.with_user(self.user).write({"external_identifier": "1234"})

    def test_group_write(self):
        exchange_record = self.create_record()
        self.user.write({"groups_id": [(4, self.group.id)]})
        exchange_record.with_user(self.user).write({"external_identifier": "1234"})
        self.assertEqual(exchange_record.external_identifier, "1234")

    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_rule_no_write(self):
        exchange_record = self.create_record()
        self.user.write({"groups_id": [(4, self.group.id)]})
        self.consumer_record.name = "no_rule"
        model = self.consumer_record
        msg = rf"not allowed to modify '{model._description}' \({model._name}\)"
        with self.assertRaisesRegex(AccessError, msg):
            exchange_record.with_user(self.user).write({"external_identifier": "1234"})

    def test_search_pagination_with_inaccessible_middle_records(self):
        """
        Regression test:
        If some records in the first page are filtered out due to access rules,
        _search must fetch additional records from next pages without truncating them.
        """

        self.user.write({"groups_id": [(4, self.group.id)]})

        # Three target records:
        # - consumer_c1 and consumer_c3 are readable: the rule of the group shows
        #   the consumer records named "test"
        # - consumer_c2 has another name and will be filtered out by the rule
        consumer_c1 = self.env["edi.exchange.consumer.test"].create({"name": "test"})
        consumer_c2 = self.env["edi.exchange.consumer.test"].create({"name": "c2"})
        consumer_c3 = self.env["edi.exchange.consumer.test"].create({"name": "test"})

        # One EDI records pointing to readable target records
        self.backend.create_record(
            "test_csv_output",
            {"model": consumer_c1._name, "res_id": consumer_c1.id},
        )

        # One EDI records pointing to a record the rule hides
        self.backend.create_record(
            "test_csv_output",
            {"model": consumer_c2._name, "res_id": consumer_c2.id},
        )

        # One EDI records pointing to readable target records
        visible_id_2 = self.backend.create_record(
            "test_csv_output",
            {"model": consumer_c3._name, "res_id": consumer_c3.id},
        ).id

        # Execute the search as a non-superuser:
        # - super()._search returns the first 2 IDs (1 visible + 1 hidden)
        # - custom logic removes the 1 hidden
        # - pagination logic fetches 1 more record from the next page
        records = (
            self.env["edi.exchange.record"]
            .with_user(self.user)
            .search([], limit=2, order="id asc")
        )

        # The result must NOT be truncated: the search should still return `
        # limit` records
        self.assertEqual(
            len(records),
            2,
            "Search results were truncated when inaccessible records were "
            "present in the first page",
        )

        # The records fetched from the second page must be present in the final result
        self.assertIn(visible_id_2, records.ids)

    def test_group_search_order(self):
        record_1 = self.create_record()
        record_2 = self.create_record()
        record_3 = self.create_record()
        self.user.write({"groups_id": [(4, self.group.id)]})
        self.assertEqual(
            [record_3.id, record_2.id, record_1.id],
            self.env["edi.exchange.record"]
            .with_user(self.user)
            .search(
                [("id", "in", (record_1 + record_2 + record_3).ids)], order="id desc"
            )
            .ids,
        )

    def test_rule_search_pages(self):
        no_rule_record = self.env["edi.exchange.consumer.test"].create(
            {"name": "no_rule"}
        )
        records = self.env["edi.exchange.record"]
        visible_records = self.env["edi.exchange.record"]
        for consumer_record in [
            no_rule_record,
            self.consumer_record,
            no_rule_record,
            self.consumer_record,
            self.consumer_record,
            no_rule_record,
            self.consumer_record,
            self.consumer_record,
            no_rule_record,
        ]:
            record = self.backend.create_record(
                "test_csv_output",
                {"model": consumer_record._name, "res_id": consumer_record.id},
            )
            records += record
            if consumer_record == self.consumer_record:
                visible_records += record
        self.user.write({"groups_id": [(4, self.group.id)]})
        model = self.env["edi.exchange.record"].with_user(self.user)
        domain = [("id", "in", records.ids)]
        visible_ids = visible_records.ids
        self.assertEqual(5, model.search_count(domain))
        self.assertEqual(visible_ids[:2], model.search(domain, limit=2, order="id").ids)
        self.assertEqual(
            visible_ids[2:4], model.search(domain, offset=2, limit=2, order="id").ids
        )
        self.assertEqual(
            visible_ids[4:], model.search(domain, offset=4, limit=2, order="id").ids
        )
        self.assertEqual(
            visible_ids[2:], model.search(domain, offset=2, order="id").ids
        )
        self.assertEqual(
            [visible_ids[4], visible_ids[3]],
            model.search(domain, limit=2, order="id desc").ids,
        )

    def test_superuser_search_pages(self):
        record_1 = self.create_record()
        record_2 = self.create_record()
        record_3 = self.create_record()
        self.assertEqual(
            [record_2.id, record_3.id],
            self.env["edi.exchange.record"]
            .search(
                [("id", "in", (record_1 + record_2 + record_3).ids)],
                offset=1,
                limit=2,
                order="id",
            )
            .ids,
        )
