import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-edi",
    description="Meta package for oca-edi Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-account_e-invoice_generate',
        'odoo13-addon-account_invoice_ubl',
        'odoo13-addon-base_ubl',
        'odoo13-addon-base_ubl_payment',
        'odoo13-addon-purchase_order_ubl',
        'odoo13-addon-purchase_stock_ubl',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
