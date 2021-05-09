import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-edi",
    description="Meta package for oca-edi Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-base_business_document_import',
        'odoo14-addon-base_edi',
        'odoo14-addon-base_ubl',
        'odoo14-addon-edi_oca',
        'odoo14-addon-purchase_order_ubl',
        'odoo14-addon-sale_order_ubl',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
