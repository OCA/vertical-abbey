Mass
====

This module manages mass requests and the planning of masses. If you want to be able to create a mass request from a donation, you should also install the module *donation_mass*.

This module has optional accounting features :
* a mass request is considered as a sort of prepaid revenue (i.e. a kind of stock) from an accounting point of view.
* when a mass is celebrated, i.e. when the mass is validated in Odoo, an account move is automatically generated (only if a Stock Account has been configure on the mass request) to move the amount of the donation associed to the mass request from the prepaid revenue account to the revenue account.

This module has been developped by the Barroux Abbey which is a Catholic Abbey. It is specific to the management of christian masses.

Configuration
=============

To configure this module, you need to:

 * check the configuration of the Mass Request Types that have been automatically created by the module
 * check the configuration of the Mass Products that have been automatically created by the module
 * create a partner for each celebrant with the option *Celebrant* activated.
 * on the company, configure the income account for the celebrated mass and the account journal that will be used for the accounting entries generated when a mass is validated.

Usage
=====

In the menu Mass > Mass Requests, create new mass requests. On each mass request, you should select the donor, the donation date, the mass request type and the intention. If the donor asked for a special date for the mass, you should also set a *Celebration Requested Date* (otherwise, leave empty). If the donor wanted the mass to be celebrated by a particular celebrant, select the celebrant (otherwise, leave empty).

Then, start the wizard *Generate Masses Journal* to generate the masses for a particular date. You can print a report that display the list of masses with the associated celebrant , donor and intention. When it is confirmed that the masses for that day have been celebrated, start the wizard *Validate Masses Journal* to validate the masses ; you won't be able to modify the masses any more.

If you want to transfer mass requests to an external celebrant with the associated donations, create a new mass requests transfer. When you validate the mass request transfer, it will generate the corresponding accounting entries ; with these accounting entries, you will be able to generate the payment of the corresponding donations to the external celebrant.

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
