import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-edi",
    description="Meta package for oca-edi Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-account_einvoice_generate>=16.0dev,<16.1dev',
        'odoo-addon-account_invoice_facturx>=16.0dev,<16.1dev',
        'odoo-addon-account_invoice_facturx_py3o>=16.0dev,<16.1dev',
        'odoo-addon-base_business_document_import>=16.0dev,<16.1dev',
        'odoo-addon-base_business_document_import_phone>=16.0dev,<16.1dev',
        'odoo-addon-base_edi>=16.0dev,<16.1dev',
        'odoo-addon-base_edifact>=16.0dev,<16.1dev',
        'odoo-addon-base_facturx>=16.0dev,<16.1dev',
        'odoo-addon-base_ubl>=16.0dev,<16.1dev',
        'odoo-addon-despatch_advice_import>=16.0dev,<16.1dev',
        'odoo-addon-pdf_helper>=16.0dev,<16.1dev',
        'odoo-addon-sale_order_import>=16.0dev,<16.1dev',
        'odoo-addon-sale_order_import_edifact>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
