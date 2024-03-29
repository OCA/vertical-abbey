# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>

{
    "name": "Donation Mass",
    "version": "14.0.1.2.0",
    "category": "Religion",
    "license": "AGPL-3",
    "summary": "Ability to create mass from donation lines",
    "author": "Barroux Abbey, Akretion, Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/vertical-abbey",
    "depends": ["donation", "mass"],
    "data": [
        "views/mass.xml",
        "views/donation.xml",
        "data/product.xml",
        "security/ir.model.access.csv",
    ],
    "demo": ["demo/demo_data.xml"],
    "installable": True,
}
