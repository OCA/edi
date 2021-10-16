import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-oca-edi",
    description="Meta package for oca-edi Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-account_e-invoice_generate',
        'odoo11-addon-account_invoice_import',
        'odoo11-addon-account_invoice_import_ubl',
        'odoo11-addon-account_invoice_ubl',
        'odoo11-addon-account_invoice_ubl_email_attachment',
        'odoo11-addon-base_business_document_import',
        'odoo11-addon-base_ubl',
        'odoo11-addon-base_ubl_payment',
        'odoo11-addon-purchase_order_ubl',
        'odoo11-addon-sale_order_import',
        'odoo11-addon-sale_order_import_ubl',
        'odoo11-addon-sale_order_ubl',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 11.0',
    ]
)
