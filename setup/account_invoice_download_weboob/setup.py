import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    install_requires=[
        'weboob==1.5',
        'dateparser==0.6.0',
        'regex==2019.12.20',
    ],
    odoo_addon={
        'external_dependencies_override': {
            'python': {
                'weboob': 'weboob==1.5',
            },
        },
    },
)
