import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    install_requires=[
        'pytesseract==0.2.5'
    ],
    odoo_addon={
        'external_dependencies_override': {
            'python': {
                'invoice2data': 'invoice2data==0.2.34',
            },
        },
    },
)
