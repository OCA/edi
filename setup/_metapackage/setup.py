import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-edi",
    description="Meta package for oca-edi Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-account_einvoice_generate',
        'odoo14-addon-account_invoice_download',
        'odoo14-addon-account_invoice_download_ovh',
        'odoo14-addon-account_invoice_export',
        'odoo14-addon-account_invoice_export_server_env',
        'odoo14-addon-account_invoice_facturx',
        'odoo14-addon-account_invoice_import',
        'odoo14-addon-account_invoice_import_facturx',
        'odoo14-addon-account_invoice_import_invoice2data',
        'odoo14-addon-account_invoice_import_simple_pdf',
        'odoo14-addon-account_invoice_import_ubl',
        'odoo14-addon-base_business_document_import',
        'odoo14-addon-base_ebill_payment_contract',
        'odoo14-addon-base_edi',
        'odoo14-addon-base_facturx',
        'odoo14-addon-base_ubl',
        'odoo14-addon-base_ubl_payment',
        'odoo14-addon-edi_account_oca',
        'odoo14-addon-edi_backend_partner_oca',
        'odoo14-addon-edi_endpoint_oca',
        'odoo14-addon-edi_exchange_template_oca',
        'odoo14-addon-edi_oca',
        'odoo14-addon-edi_storage_oca',
        'odoo14-addon-edi_webservice_oca',
        'odoo14-addon-endpoint',
        'odoo14-addon-endpoint_auth_api_key',
        'odoo14-addon-endpoint_route_handler',
        'odoo14-addon-partner_identification_import',
        'odoo14-addon-purchase_order_ubl',
        'odoo14-addon-sale_order_customer_free_ref',
        'odoo14-addon-sale_order_import',
        'odoo14-addon-sale_order_import_ubl',
        'odoo14-addon-sale_order_import_ubl_customer_free_ref',
        'odoo14-addon-sale_order_ubl',
        'odoo14-addon-webservice',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
