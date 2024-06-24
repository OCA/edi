import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-edi",
    description="Meta package for oca-edi Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-account_einvoice_generate>=15.0dev,<15.1dev',
        'odoo-addon-account_invoice_facturx>=15.0dev,<15.1dev',
        'odoo-addon-base_edi>=15.0dev,<15.1dev',
        'odoo-addon-base_facturx>=15.0dev,<15.1dev',
        'odoo-addon-base_import_pdf_by_template>=15.0dev,<15.1dev',
        'odoo-addon-base_ubl>=15.0dev,<15.1dev',
        'odoo-addon-edi_account_oca>=15.0dev,<15.1dev',
        'odoo-addon-edi_backend_partner_oca>=15.0dev,<15.1dev',
        'odoo-addon-edi_exchange_template_oca>=15.0dev,<15.1dev',
        'odoo-addon-edi_oca>=15.0dev,<15.1dev',
        'odoo-addon-edi_stock_oca>=15.0dev,<15.1dev',
        'odoo-addon-edi_storage_oca>=15.0dev,<15.1dev',
        'odoo-addon-edi_voxel_account_invoice_oca>=15.0dev,<15.1dev',
        'odoo-addon-edi_voxel_oca>=15.0dev,<15.1dev',
        'odoo-addon-edi_voxel_sale_order_import_oca>=15.0dev,<15.1dev',
        'odoo-addon-edi_voxel_sale_secondary_unit_oca>=15.0dev,<15.1dev',
        'odoo-addon-edi_voxel_secondary_unit_oca>=15.0dev,<15.1dev',
        'odoo-addon-edi_voxel_stock_picking_oca>=15.0dev,<15.1dev',
        'odoo-addon-edi_voxel_stock_picking_secondary_unit_oca>=15.0dev,<15.1dev',
        'odoo-addon-edi_webservice_oca>=15.0dev,<15.1dev',
        'odoo-addon-pdf_helper>=15.0dev,<15.1dev',
        'odoo-addon-test_base_import_pdf_by_template>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
