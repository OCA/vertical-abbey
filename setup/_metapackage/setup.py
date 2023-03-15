import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-vertical-abbey",
    description="Meta package for oca-vertical-abbey Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-donation_mass',
        'odoo14-addon-donation_stay',
        'odoo14-addon-mass',
        'odoo14-addon-stay',
        'odoo14-addon-stay_report_py3o',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
