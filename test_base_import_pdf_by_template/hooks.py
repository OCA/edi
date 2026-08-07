# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    # Template changes
    generic_product = env.ref("test_base_import_pdf_by_template.generic_product")
    product_model_name = "product.product"
    env.ref("test_base_import_pdf_by_template.po_decathlon_line_product_id").write(
        {"default_value": f"{product_model_name},{generic_product.id}"}
    )
