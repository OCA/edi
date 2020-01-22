import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-edi",
    description="Meta package for oca-edi Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-account_e-invoice_generate',
        'odoo12-addon-account_invoice_import',
        'odoo12-addon-account_invoice_ubl',
        'odoo12-addon-account_invoice_ubl_email_attachment',
        'odoo12-addon-base_business_document_import',
        'odoo12-addon-base_business_document_import_phone',
        'odoo12-addon-base_ubl',
        'odoo12-addon-base_ubl_payment',
        'odoo12-addon-sale_order_ubl',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
