import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-oca-edi",
    description="Meta package for oca-edi Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-account_e-invoice_generate',
        'odoo11-addon-base_business_document_import',
        'odoo11-addon-base_ubl',
        'odoo11-addon-base_ubl_payment',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
