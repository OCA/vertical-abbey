This module adds the ability to create mass requests from donation
lines.

When a donation is validated with a mass in one of the donation lines,
a new mass request is automatically created and the account move
associated to the donation will send the amount of that donation line
to a stock account. When the mass is celebrated, i.e. when the mass
is validated in Odoo, an accounting entry is generated from the stock
account to a revenue account.
