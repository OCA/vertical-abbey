This module manages mass requests and the planning of masses. If you want to be able to create a mass request from a donation, you should also install the module *donation_mass*.

This module has an impact on accounting:
* a mass request in waiting or started state is considered as a stock from an accounting point of view.
* when a mass is celebrated, i.e. when the mass is validated in Odoo, an account move is automatically generated to move the amount of the donation associed to the mass line from the stock account to the revenue account.

This module also allows to transfer masses to an external celebrant. When validating the mass transfer, a journal entry is created that moves the corresponding donation amount from the mass stock account to the payable account of the external celebrant.

This module has been developped by the `Barroux Abbey <https://www.barroux.org/>`_ which is a French Catholic Abbey. It is specific to the management of christian masses.
