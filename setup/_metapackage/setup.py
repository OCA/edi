import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo8-addons-oca-edi",
    description="Meta package for oca-edi Odoo addons",
    version=version,
    install_requires=[
        'odoo8-addon-account_invoice_import',
        'odoo8-addon-account_invoice_import_invoice2data',
        'odoo8-addon-account_invoice_import_ubl',
        'odoo8-addon-account_invoice_import_zugferd',
        'odoo8-addon-account_invoice_ubl',
        'odoo8-addon-account_invoice_zugferd',
        'odoo8-addon-base_business_document_import',
        'odoo8-addon-base_business_document_import_phone',
        'odoo8-addon-base_business_document_import_stock',
        'odoo8-addon-base_ubl',
        'odoo8-addon-base_ubl_payment',
        'odoo8-addon-base_zugferd',
        'odoo8-addon-purchase_order_import',
        'odoo8-addon-purchase_order_import_ubl',
        'odoo8-addon-purchase_order_ubl',
        'odoo8-addon-sale_commercial_partner',
        'odoo8-addon-sale_order_import',
        'odoo8-addon-sale_order_import_csv',
        'odoo8-addon-sale_order_import_ubl',
        'odoo8-addon-sale_order_ubl',
        'odoo8-addon-sale_stock_order_import',
        'odoo8-addon-supplier_inventory_import_ubl',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 8.0',
    ]
)
