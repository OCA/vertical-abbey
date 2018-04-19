import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo8-addons-oca-vertical-abbey",
    description="Meta package for oca-vertical-abbey Odoo addons",
    version=version,
    install_requires=[
        'odoo8-addon-donation_mass',
        'odoo8-addon-donation_stay',
        'odoo8-addon-mass',
        'odoo8-addon-stay',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
