import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-vertical-abbey",
    description="Meta package for oca-vertical-abbey Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-donation_mass>=16.0dev,<16.1dev',
        'odoo-addon-mass>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
