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
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
