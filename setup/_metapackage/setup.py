import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-oca-vertical-abbey",
    description="Meta package for oca-vertical-abbey Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-donation_mass',
        'odoo10-addon-donation_stay',
        'odoo10-addon-mass',
        'odoo10-addon-stay',
        'odoo10-addon-stay_report_py3o',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 10.0',
    ]
)
