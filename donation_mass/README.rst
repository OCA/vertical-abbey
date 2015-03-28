Donation Mass
=============

This module adds the ability to create mass requests from donation
lines.

When a donation is validated with a mass in one of the donation lines,
a new mass request is automatically created and the account move
associated to the donation will send the amount of that donation line
to a provision account. When the mass is celebrated, i.e. when the mass
is validated in Odoo, an accounting entry is generated from the provision
account to a revenue account.

It has been developped by brother Bernard and brother Irénée from
Barroux Abbey and by Alexis de Lattre from Akretion.

Configuration
=============

Check that the mass products have the option *Is a Donation* active.
On the mass product, you should configure the provision account as *Income Account*.

Usage
=====

When you create a new donation line, if you select a mass product,
you can specify the mass intention. If the donor wants the mass to be
celebrated by a particular celebrant, you can also specify a celebrant
on the donation line (otherwise, leave empty). If the donor wants the
mass to be celebrated at a particular date, you can also specify a
Celebration Requested Date on the donation line (otherwise, leave empty).

Credits
=======

Contributors
------------

* Brother Bernard <informatique - at - barroux.org>
* Brother Irénée (Barroux Abbey)
* Alexis de Lattre <alexis.delattre@akretion.com>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose mission is to support the collaborative development of Odoo features and promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
