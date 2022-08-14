# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import os

import xmlunittest

from odoo import fields
from odoo.tests.common import Form, SavepointCase

from odoo.addons.sale_order_import_ubl.tests.common import get_test_data


def get_xml_handler(backend, schema_path, model=None):
    model = model or backend._name
    return backend._find_component(
        model,
        ["edi.xml"],
        work_ctx={"schema_path": schema_path},
        safe=False,
    )


def flatten(txt):
    return "".join([x.strip() for x in txt.splitlines()])


def dev_write_example_file(filename, content, test_file=None):
    test_file = test_file or __file__
    from pathlib import Path

    path = Path(test_file).parent / ("examples/test." + filename)
    with open(path, "w") as out:
        out.write(content)


def read_test_file(filename):
    path = os.path.join(os.path.dirname(__file__), "examples", filename)
    with open(path, "r") as thefile:
        return thefile.read()


# TODO: reuse common class from edi_xml_oca
class XMLBaseTestCase(SavepointCase, xmlunittest.XmlTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.backend = cls._get_backend()

    @classmethod
    def _get_backend(cls):
        raise NotImplementedError()


class OrderMixin(object):
    @classmethod
    def _create_sale_order(cls, values, view=None):
        """Create a sale order

        :return: sale order
        """
        form = Form(cls.env["sale.order"], view=view)
        form.commitment_date = fields.Date.today()
        for k, v in values.items():
            setattr(form, k, v)
        return form.save()

    @classmethod
    def _create_sale_order_line(cls, order, view=None, **kw):
        """
        Create a sale order line for give order
        :return: line
        """
        values = {}
        values.update(kw)
        form = Form(order, view=view)
        with form.order_line.new() as form_line:
            for k, v in values.items():
                setattr(form_line, k, v)
        return form.save()


class TestCaseBase(XMLBaseTestCase, OrderMixin):
    @classmethod
    def _setup_order(cls):
        cls.product_a = cls.env.ref("product.product_product_4")
        cls.product_a.barcode = "1" * 14
        cls.product_b = cls.env.ref("product.product_product_4b")
        cls.product_b.barcode = "2" * 14
        cls.product_c = cls.env.ref("product.product_product_4c")
        cls.product_c.barcode = "3" * 14
        cls.sale = cls._create_sale_order(
            {
                "partner_id": cls.env.ref("base.res_partner_10"),
                "commitment_date": "2022-07-29",
            }
        )
        lines = [
            {"product_id": cls.product_a, "product_uom_qty": 300},
            {"product_id": cls.product_b, "product_uom_qty": 200},
            {"product_id": cls.product_c, "product_uom_qty": 100},
        ]
        for line in lines:
            cls._create_sale_order_line(cls.sale, **line)

        cls.sale.action_confirm()


class OrderInboundTestMixin:
    @classmethod
    def _setup_inbound_order(cls, backend):
        cls.exc_type_in = cls.env.ref("edi_sale_ubl_oca.edi_exc_type_order_in")
        cls.exc_type_out = cls.env.ref(
            "edi_sale_ubl_oca.edi_exc_type_order_response_out"
        )
        cls.exc_type_in.backend_id = backend
        cls.exc_type_out.backend_id = backend
        cls.exc_record_in = backend.create_record(
            cls.exc_type_in.code, {"edi_exchange_state": "input_received"}
        )
        cls.ubl_data = get_test_data(cls.env)
        fname = "UBL-Order-2.1-Example.xml"
        cls.order_data = cls.ubl_data[fname]
        fcontent = cls.order_data._get_content()
        cls.exc_record_in._set_file_content(fcontent)
        cls.err_msg_already_imported = "Sales order has already been imported before"

    def _find_order(self):
        return self.env["sale.order"].search(
            [
                ("client_order_ref", "=", self.order_data.client_order_ref),
                ("commercial_partner_id", "=", self.order_data.partner.parent_id.id),
            ]
        )
