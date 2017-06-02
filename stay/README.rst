.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

====
Stay
====

This module manages stays ; it handles lunches, dinners and bed nights.

It has been initially developped by the Barroux Abbey (http://www.barroux.org) to manage the stays of the guests at the Abbey.

Configuration
=============

To configure this module, you need to:

 * create the Rooms
 * create the Refectories
 * configure the default Refectory on the company.

Usage
=====

To use this module, go to the menu Stays > Stays and start to register the future stays.

Every day, start the wizard *Generate Journal* to generate the stay lines for the next day. You can then print the stay report via the wizard *Print Journal* to have a printed paper that you can give to the cook for example.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/181/10.0

Known issues / Roadmap
======================

This module doesn't have advanced capacity management : when you create a new stay, it will not check that you have enough capacity for it. It is only when you generate the journal that it will check that each room doesn't have more guest than it's capacity.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/vertical-abbey/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Brother Bernard <informatique - at - barroux.org>
* Brother Irénée (Barroux Abbey)
* Alexis de Lattre <alexis.delattre@akretion.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
