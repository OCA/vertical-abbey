# Copyright 2014-2021 Barroux Abbey (www.barroux.org)
# Copyright 2014-2021 Akretion France (www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class MassRequestType(models.Model):
    _name = "mass.request.type"
    _description = "Types of Mass Requests"
    _order = "name"

    name = fields.Char(string="Mass Request Type", required=True)
    code = fields.Char(string="Mass Request Code", size=5)
    quantity = fields.Integer()
    uninterrupted = fields.Boolean()
    # True for Novena and Gregorian series ; False for others


class ReligiousCommunity(models.Model):
    _name = "religious.community"
    _description = "Religious Community"

    name = fields.Char(string="Community Code", size=12, required=True)
    long_name = fields.Char(string="Community Name")
    active = fields.Boolean(default=True)


class MassRequest(models.Model):
    _name = "mass.request"
    _inherit = "analytic.mixin"
    _description = "Mass Request"
    _order = "id desc"
    _check_company_auto = True

    partner_id = fields.Many2one(
        "res.partner", string="Donor", required=True, ondelete="restrict", index=True
    )
    celebrant_id = fields.Many2one(
        "res.partner",
        domain=[("celebrant", "=", "internal")],
        ondelete="restrict",
        index=True,
        help="If the donor want the mass to be celebrated by a particular "
        "celebrant, select it here. Otherwise, leave empty.",
    )
    donation_date = fields.Date(required=True)
    request_date = fields.Date(
        string="Celebration Requested Date",
        help="If the donor want the mass to be celebrated at a particular "
        "date, select it here. Otherwise, leave empty.",
    )
    product_id = fields.Many2one(
        "product.product",
        string="Mass Product",
        check_company=True,
        domain="[('company_id', 'in', (False, company_id)), "
        "('detailed_type', '=', 'donation_mass')]",
        required=True,
        readonly=True,
        ondelete="restrict",
        states={"waiting": [("readonly", False)]},
    )
    type_id = fields.Many2one(
        related="product_id.mass_request_type_id",
        store=True,
        string="Mass Request Type",
    )
    uninterrupted = fields.Boolean(related="type_id.uninterrupted")
    offering = fields.Monetary(
        currency_field="company_currency_id",
        readonly=True,
        states={"waiting": [("readonly", False)]},
        help="The total offering amount in company currency.",
    )
    unit_offering = fields.Monetary(
        compute="_compute_unit_offering",
        store=True,
        string="Offering per Mass",
        currency_field="company_currency_id",
        help="This field is the offering amount per mass in company currency.",
    )
    stock_account_id = fields.Many2one(
        "account.account",
        check_company=True,
        required=True,
        domain="[('company_id', '=', company_id), ('deprecated', '=', False)]",
        default=lambda self: self.env.company.mass_stock_account_id,
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        ondelete="restrict",
        default=lambda self: self.env.company,
    )
    company_currency_id = fields.Many2one(
        related="company_id.currency_id", string="Company Currency", store=True
    )
    quantity = fields.Integer(
        default=1, readonly=True, states={"waiting": [("readonly", False)]}
    )
    # quantity = quantity in the donation line
    mass_quantity = fields.Integer(
        compute="_compute_total_qty", string="Total Mass Quantity", store=True
    )
    intention = fields.Char()
    line_ids = fields.One2many("mass.line", "request_id", string="Mass Lines")
    state = fields.Selection(
        [
            ("waiting", "Waiting"),
            ("started", "Started"),
            ("transfered", "Transfered"),
            ("done", "Done"),
        ],
        compute="_compute_state_mass_remaining_quantity",
        store=True,
    )
    mass_remaining_quantity = fields.Integer(
        compute="_compute_state_mass_remaining_quantity",
        store=True,
    )
    remaining_offering = fields.Monetary(
        compute="_compute_state_mass_remaining_quantity",
        store=True,
        currency_field="company_currency_id",
    )
    transfer_id = fields.Many2one(
        "mass.request.transfer",
        string="Transfer Operation",
        readonly=True,
        check_company=True,
    )

    @api.depends(
        "type_id", "type_id.quantity", "quantity", "line_ids.request_id", "transfer_id"
    )
    def _compute_state_mass_remaining_quantity(self):
        for req in self:
            total_qty = req.type_id.quantity * req.quantity
            remaining_qty = total_qty
            if req.line_ids:
                remaining_qty -= len(req.line_ids)
            if remaining_qty < 0:
                remaining_qty = 0
            state = "waiting"
            if req.transfer_id:
                state = "transfered"
                remaining_qty = 0
            elif total_qty:
                if remaining_qty == 0:
                    state = "done"
                elif remaining_qty < total_qty and req.uninterrupted:
                    state = "started"
            req.state = state
            req.mass_remaining_quantity = remaining_qty
            req.remaining_offering = remaining_qty * req.unit_offering

    @api.depends("type_id", "type_id.quantity", "quantity", "offering")
    def _compute_unit_offering(self):
        for req in self:
            total_qty = req.type_id.quantity * req.quantity
            if total_qty:
                req.unit_offering = req.offering / total_qty
            else:
                req.unit_offering = 0.0

    @api.depends("type_id", "type_id.quantity", "quantity")
    def _compute_total_qty(self):
        for req in self:
            req.mass_quantity = req.type_id.quantity * req.quantity

    @api.depends("product_id")
    def _compute_analytic_distribution(self):
        for req in self:
            product = req.product_id
            if product:
                account = product.with_company(
                    req.company_id.id
                )._get_product_accounts()["income"]
                distribution = self.env[
                    "account.analytic.distribution.model"
                ]._get_distribution(
                    {
                        "product_id": product.id,
                        "product_categ_id": product.categ_id.id,
                        "account_prefix": account and account.code or False,
                        "company_id": req.company_id.id,
                    }
                )
                req.analytic_distribution = distribution or req.analytic_distribution

    def name_get(self):
        res = []
        for request in self:
            res.append(
                (
                    request.id,
                    "[%dx%s] %s"
                    % (
                        request.quantity,
                        request.type_id.code,
                        request.partner_id.display_name,
                    ),
                )
            )
        return res

    @api.onchange("product_id")
    def product_id_change(self):
        if self.product_id:
            self.offering = self.product_id.list_price

    def unlink(self):
        for request in self:
            if request.state != "waiting":
                raise UserError(
                    _(
                        "Cannot delete mass request '%s' because "
                        "it is not in Waiting state."
                    )
                    % request.display_name
                )
        return super().unlink()


class MassLine(models.Model):
    _name = "mass.line"
    _description = "Mass Lines"
    _order = "date desc, id desc"

    request_id = fields.Many2one(
        "mass.request",
        string="Mass Request",
        ondelete="cascade",
        states={"done": [("readonly", True)]},
        index=True,
    )
    date = fields.Date(
        string="Celebration Date", required=True, states={"done": [("readonly", True)]}
    )
    partner_id = fields.Many2one(
        "res.partner", related="request_id.partner_id", string="Donor", store=True
    )
    intention = fields.Char(related="request_id.intention", string="Intention")
    company_id = fields.Many2one(
        "res.company", related="request_id.company_id", store=True
    )
    company_currency_id = fields.Many2one(
        "res.currency",
        related="request_id.company_id.currency_id",
        string="Company Currency",
        store=True,
    )
    request_date = fields.Date(
        related="request_id.request_date", store=True, string="Mass Request Date"
    )
    product_id = fields.Many2one(related="request_id.product_id", store=True)
    type_id = fields.Many2one(
        related="request_id.product_id.mass_request_type_id", store=True
    )
    unit_offering = fields.Monetary(
        string="Offering",
        currency_field="company_currency_id",
        states={"done": [("readonly", True)]},
    )
    celebrant_id = fields.Many2one(
        "res.partner",
        required=True,
        index=True,
        domain=[("celebrant", "=", "internal")],
        ondelete="restrict",
        states={"done": [("readonly", True)]},
    )
    conventual_id = fields.Many2one(
        "religious.community",
        string="Conventual",
        ondelete="restrict",
        index=True,
        states={"done": [("readonly", True)]},
    )
    move_id = fields.Many2one("account.move", string="Journal Entry", readonly=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("done", "Done"),
        ],
        default="draft",
        readonly=True,
    )

    def unlink(self):
        # Get the last journal date
        mass_line = self.search([], limit=1, order="date desc")
        if mass_line:  # we should always have 1, unless if self is empty
            last_date = mass_line.date
            for mass in self:
                if mass.state == "done":
                    raise UserError(
                        _(
                            "Cannot delete mass line dated %(date)s for %(partner)s "
                            "because it is in 'Done' state.",
                            date=format_date(self.env, mass.date),
                            partner=mass.partner_id.display_name,
                        )
                    )
                if mass.type_id.uninterrupted and mass.date < last_date:
                    raise UserError(
                        _(
                            "Cannot delete mass dated %(date)s for %(partner)s "
                            "because it is a %(mass_type_name)s which is an "
                            "uninterrupted mass.",
                            date=format_date(self.env, mass.date),
                            partner=mass.partner_id.display_name,
                            mass_type_name=mass.type_id.display_name,
                        )
                    )
        return super().unlink()


class MassRequestTransfer(models.Model):
    _name = "mass.request.transfer"
    _description = "Transfered Mass Requests"
    _rec_name = "number"
    _check_company_auto = True

    def name_get(self):
        state2label = dict(self.fields_get("state", "selection")["state"]["selection"])
        res = []
        for trf in self:
            name = "%s %s (%s)" % (
                trf.celebrant_id.display_name,
                format_date(self.env, trf.transfer_date),
                state2label.get(trf.state),
            )
            res.append((trf.id, name))
        return res

    @api.depends(
        "mass_request_ids",
        "mass_request_ids.mass_quantity",
        "mass_request_ids.offering",
    )
    def _compute_transfer_totals(self):
        for trf in self:
            amount_total = 0.0
            mass_total = 0
            for request in trf.mass_request_ids:
                amount_total += request.offering
                mass_total += request.mass_quantity
            trf.amount_total = amount_total
            trf.mass_total = mass_total

    number = fields.Char(string="Transfer Number", readonly=True)
    celebrant_id = fields.Many2one(
        "res.partner",
        required=True,
        index=True,
        domain=[("celebrant", "=", "external")],
        states={"done": [("readonly", True)]},
        ondelete="restrict",
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        ondelete="restrict",
        states={"done": [("readonly", True)]},
        default=lambda self: self.env.company,
    )
    company_currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        string="Company Currency",
        store=True,
    )
    transfer_date = fields.Date(
        required=True,
        states={"done": [("readonly", True)]},
        default=fields.Date.context_today,
    )
    mass_request_ids = fields.One2many(
        "mass.request",
        "transfer_id",
        string="Mass Requests",
        states={"done": [("readonly", True)]},
    )
    move_id = fields.Many2one(
        "account.move", string="Journal Entry", readonly=True, check_company=True
    )
    amount_total = fields.Monetary(
        compute="_compute_transfer_totals",
        type="float",
        currency_field="company_currency_id",
        store=True,
    )
    mass_total = fields.Integer(
        compute="_compute_transfer_totals", string="Total Mass Quantity", store=True
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("done", "Done"),
        ],
        readonly=True,
        default="draft",
    )

    @api.model
    def _prepare_mass_transfer_move(self, number):
        movelines = []
        stock_aml = defaultdict(float)  # key = account_id, value = amount
        for request in self.mass_request_ids:
            stock_account_id = request.stock_account_id.id or False
            if not stock_account_id:
                raise UserError(
                    _("Missing stock account on mass request %s.")
                    % request.display_name
                )
            if stock_account_id:
                stock_aml[stock_account_id] += request.offering

        partner_id = self.celebrant_id.id
        for stock_account_id, stock_amount in stock_aml.items():
            movelines.append(
                (
                    0,
                    0,
                    {
                        "credit": 0,
                        "debit": stock_amount,
                        "account_id": stock_account_id,
                        "partner_id": partner_id,
                    },
                )
            )

        # counter-part
        movelines.append(
            (
                0,
                0,
                {
                    "debit": 0,
                    "credit": self.amount_total,
                    "account_id": self.celebrant_id.property_account_payable_id.id,
                    "partner_id": partner_id,
                    "display_type": "payment_term",
                },
            )
        )

        vals = {
            "journal_id": self.company_id.mass_validation_journal_id.id,
            # Same journal as validation journal ?
            "date": self.transfer_date,
            "ref": number,
            "line_ids": movelines,
            "company_id": self.company_id.id,
        }
        return vals

    def validate(self):
        self.ensure_one()
        if not self.mass_request_ids:
            raise UserError(
                _(
                    "Cannot validate mass request transfer %s because it has no "
                    "mass requests."
                )
            )
        if not self.company_id.mass_validation_journal_id:
            raise UserError(
                _("The 'Mass Validation Journal' is not set on company '%s'.")
                % self.company_id.display_name
            )

        transfer_vals = {"state": "done"}
        number = self.number
        if not number:
            number = self.env["ir.sequence"].next_by_code("mass.request.transfer")
            transfer_vals["number"] = number

        # Create account move
        move_vals = self._prepare_mass_transfer_move(number)
        move = self.env["account.move"].create(move_vals)
        if self.company_id.mass_post_move:
            move._post(soft=False)

        transfer_vals["move_id"] = move.id
        self.write(transfer_vals)

    def back_to_draft(self):
        self.ensure_one()
        if self.move_id:
            self.move_id.button_cancel()
            self.move_id.unlink()
        self.state = "draft"

    def unlink(self):
        for trf in self:
            if trf.state == "done":
                raise UserError(
                    _(
                        "Cannot delete mass request transfer dated %(date)s for "
                        "%(celebrant)s because it is in 'Done' state.",
                        date=format_date(self.env, trf.transfer_date),
                        celebrant=trf.celebrant_id.display_name,
                    )
                )
        return super().unlink()
