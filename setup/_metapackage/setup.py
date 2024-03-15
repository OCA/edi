import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-edi",
    description="Meta package for oca-edi Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-account_e-invoice_generate',
        'odoo12-addon-account_invoice_download',
        'odoo12-addon-account_invoice_download_ovh',
        'odoo12-addon-account_invoice_facturx',
        'odoo12-addon-account_invoice_facturx_py3o',
        'odoo12-addon-account_invoice_import',
        'odoo12-addon-account_invoice_import_facturx',
        'odoo12-addon-account_invoice_import_invoice2data',
        'odoo12-addon-account_invoice_import_ubl',
        'odoo12-addon-account_invoice_ubl',
        'odoo12-addon-account_invoice_ubl_email_attachment',
        'odoo12-addon-base_business_document_import',
        'odoo12-addon-base_business_document_import_phone',
        'odoo12-addon-base_business_document_import_stock',
        'odoo12-addon-base_edi',
        'odoo12-addon-base_facturx',
        'odoo12-addon-base_ubl',
        'odoo12-addon-base_ubl_payment',
        'odoo12-addon-edi_oca',
        'odoo12-addon-purchase_order_ubl',
        'odoo12-addon-purchase_stock_ubl',
        'odoo12-addon-sale_order_import',
        'odoo12-addon-sale_order_ubl',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 12.0',
    ]
)
