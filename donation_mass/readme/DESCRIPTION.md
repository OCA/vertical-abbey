This module manages mass requests and the planning of masses. Mass requests can be created manually or from a donation.

This module has an impact on accounting: \* a mass request in waiting or
started state is considered as a stock from an accounting point of view.
\* when a mass is celebrated, i.e. when the mass is validated in Odoo,
an account move is automatically generated to move the amount of the
donation associed to the mass line from the stock account to the revenue
account.

When a donation is validated with a mass in one of the donation lines, a
new mass request is automatically created and the account move
associated to the donation will send the amount of that donation line to
a stock account. When the mass is celebrated, i.e. when the mass is
validated in Odoo, an accounting entry is generated from the stock
account to a revenue account.

This module also allows to transfer masses to an external celebrant.
When validating the mass transfer, a journal entry is created that moves
the corresponding donation amount from the mass stock account to the
payable account of the external celebrant.

This module has been developped by the [Barroux
Abbey](https://www.barroux.org/) which is a French Catholic Abbey. It is
specific to the management of christian masses.


