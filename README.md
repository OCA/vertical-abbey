[![Build Status](https://travis-ci.org/OCA/vertical-abbey.svg?branch=10.0)](https://travis-ci.org/OCA/vertical-abbey)
[![Coverage Status](https://coveralls.io/repos/OCA/vertical-abbey/badge.png?branch=10.0)](https://coveralls.io/r/OCA/vertical-abbey?branch=10.0)

# Vertical Abbey - The Philemon project

![Logo of the Philemon project](http://people.via.ecp.fr/~alexis/philemon-logo-192.png "Philemon logo")

The Philemon project develops Odoo modules for Abbeys.

The two main modules of the Philemon project are:
* *stay*: manage the stay of guests at the Abbey. Handles lunches, dinners and bed nights.
* *mass*: manages mass requests and the planning of masses.

Two other modules *donation_stay* and *donation_mass* connect the management of stay and masses to donations. The Odoo modules for donations are available in the [Donation OCA project](https://github.com/OCA/donation).

These modules and the donation modules have been developped by the
[Barroux Abbey](http://www.barroux.org/), a Benedictine Abbey located
near the [Mont Ventoux](http://en.wikipedia.org/wiki/Mont_Ventoux) in
France, who decided to publish these modules so that they can benefit
to other abbeys and other christian organisations. They are used in
production at the Barroux Abbey since January 1st 2015.

The main developpers of the project are:
* Brother Bernard (Barroux Abbey)
* Brother Irénée (Barroux Abbey)
* Alexis de Lattre (Akretion)

Please refer to the README of each module to have more information about
how to configure and use the modules.

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[donation_mass](donation_mass/) | 10.0.1.0.0 |  | Ability to create mass from donation lines
[donation_stay](donation_stay/) | 10.0.1.0.0 |  | Create donations from a stay
[mass](mass/) | 10.0.1.0.1 |  | Manage Mass
[stay](stay/) | 10.0.1.0.0 |  | Simple management of stays and meals
[stay_report_py3o](stay_report_py3o/) | 10.0.1.0.0 |  | Replace Qweb report by Py3o report on stay module

[//]: # (end addons)
