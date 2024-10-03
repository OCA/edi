# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    # Template changes
    generic_product = env.ref("test_base_import_pdf_by_template.generic_product")
    template_po_decathlon = env.ref("test_base_import_pdf_by_template.po_decathlon")
    template_po_decathlon.write({"auto_detect_pattern": r"(?<=ESA79935607)[\S\s]*"})
    product_model_name = "product.product"
    env.ref("test_base_import_pdf_by_template.po_decathlon_line_product_id").write(
        {"default_value": f"{product_model_name},{generic_product.id}"}
    )
    template_invoice_tecnativa = env.ref(
        "test_base_import_pdf_by_template.invoice_tecnativa"
    )
    template_invoice_tecnativa.write(
        {"auto_detect_pattern": r"(?<=B 8 7 5 3 0 4 3 2)[\S\s]*"}
    )
    env.ref("test_base_import_pdf_by_template.invoice_tecnativa_line_product_id").write(
        {"default_value": f"{product_model_name},{generic_product.id}"}
    )
