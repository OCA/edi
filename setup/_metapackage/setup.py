import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-oca-edi",
    description="Meta package for oca-edi Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-account_e-invoice_generate',
        'odoo10-addon-account_invoice_factur-x',
        'odoo10-addon-account_invoice_factur-x_py3o',
        'odoo10-addon-account_invoice_import',
        'odoo10-addon-account_invoice_import_factur-x',
        'odoo10-addon-account_invoice_import_invoice2data',
        'odoo10-addon-account_invoice_import_ubl',
        'odoo10-addon-account_invoice_ubl',
        'odoo10-addon-account_invoice_ubl_py3o',
        'odoo10-addon-base_business_document_import',
        'odoo10-addon-base_business_document_import_phone',
        'odoo10-addon-base_business_document_import_stock',
        'odoo10-addon-base_ubl',
        'odoo10-addon-base_ubl_payment',
        'odoo10-addon-base_zugferd',
        'odoo10-addon-purchase_order_import',
        'odoo10-addon-purchase_order_import_ubl',
        'odoo10-addon-purchase_order_ubl',
        'odoo10-addon-purchase_order_ubl_py3o',
        'odoo10-addon-sale_order_import',
        'odoo10-addon-sale_order_import_csv',
        'odoo10-addon-sale_order_import_ubl',
        'odoo10-addon-sale_order_ubl',
        'odoo10-addon-sale_order_ubl_py3o',
        'odoo10-addon-sale_stock_order_import',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
