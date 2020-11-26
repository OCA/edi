import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-edi",
    description="Meta package for oca-edi Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-account_e-invoice_generate',
        'odoo13-addon-account_invoice_export',
        'odoo13-addon-account_invoice_facturx',
        'odoo13-addon-account_invoice_facturx_py3o',
        'odoo13-addon-account_invoice_ubl',
        'odoo13-addon-account_invoice_ubl_email_attachment',
        'odoo13-addon-base_business_document_import',
        'odoo13-addon-base_ebill_payment_contract',
        'odoo13-addon-base_edi',
        'odoo13-addon-base_facturx',
        'odoo13-addon-base_ubl',
        'odoo13-addon-base_ubl_payment',
        'odoo13-addon-edi',
        'odoo13-addon-edi_exchange_template',
        'odoo13-addon-edi_voxel',
        'odoo13-addon-edi_voxel_account_invoice',
        'odoo13-addon-edi_voxel_sale_order_import',
        'odoo13-addon-edi_voxel_stock_picking',
        'odoo13-addon-partner_identification_import',
        'odoo13-addon-purchase_order_ubl',
        'odoo13-addon-purchase_stock_ubl',
        'odoo13-addon-sale_order_import',
        'odoo13-addon-sale_order_import_ubl',
        'odoo13-addon-sale_order_ubl',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
