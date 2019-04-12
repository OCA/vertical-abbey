# -*- coding: utf-8 -*-
# © 2014-2017 Barroux Abbey (www.barroux.org)
# © 2014-2017 Akretion France (www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    celebrant = fields.Boolean(string='Celebrant')
    # A celebrant to which we transfer mass is celebrant + supplier


class MassRequestType(models.Model):
    _name = "mass.request.type"
    _description = 'Types of Mass Requests'
    _order = 'name'

    name = fields.Char(string='Mass Request Type', required=True)
    code = fields.Char(string='Mass Request Code', size=5)
    quantity = fields.Integer(string='Quantity')
    uninterrupted = fields.Boolean(string='Uninterrupted')
    # True for Novena and Gregorian series ; False for others


class ProductTemplate(models.Model):
    _inherit = "product.template"

    mass = fields.Boolean(string='Is a Mass')
    mass_request_type_id = fields.Many2one(
        'mass.request.type', string='Mass Request Type', ondelete='restrict')

    @api.onchange('mass')
    def mass_change(self):
        if self.mass:
            self.type = 'service'
            self.sale_ok = False


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('mass')
    def mass_change(self):
        if self.mass:
            self.type = 'service'
            self.sale_ok = False


class ReligiousCommunity(models.Model):
    _name = "religious.community"
    _description = "Religious Community"

    name = fields.Char(string='Community Code', size=12, required=True)
    long_name = fields.Char(string='Community Name')
    active = fields.Boolean(string='Active', default=True)


class MassRequest(models.Model):
    _name = 'mass.request'
    _description = 'Mass Request'
    _order = 'id desc'

    @api.one
    @api.depends(
        'type_id', 'type_id.quantity', 'quantity',
        'line_ids.request_id', 'transfer_id')
    def _compute_state_mass_remaining_quantity(self):
        total_qty = self.type_id.quantity * self.quantity
        remaining_qty = total_qty
        if self.line_ids:
            remaining_qty -= len(self.line_ids)
        if remaining_qty < 0:
            remaining_qty = 0
        state = 'waiting'
        if self.transfer_id:
            state = 'transfered'
            remaining_qty = 0
        elif total_qty:
            if remaining_qty == 0:
                state = 'done'
            elif remaining_qty < total_qty and self.uninterrupted:
                state = 'started'
        self.state = state
        self.mass_remaining_quantity = remaining_qty
        self.remaining_offering = remaining_qty * self.unit_offering

    @api.one
    @api.depends('type_id', 'type_id.quantity', 'quantity', 'offering')
    def _compute_unit_offering(self):
        total_qty = self.type_id.quantity * self.quantity
        if total_qty:
            self.unit_offering = self.offering / total_qty
        else:
            self.unit_offering = 0.0

    @api.one
    @api.depends('type_id', 'type_id.quantity', 'quantity')
    def _compute_total_qty(self):
        self.mass_quantity = self.type_id.quantity * self.quantity

    def name_get(self):
        res = []
        for request in self:
            res.append((
                request.id,
                u'[%dx%s] %s' % (
                    request.quantity,
                    request.type_id.code,
                    request.partner_id.name,
                    )))
        return res

    partner_id = fields.Many2one(
        'res.partner', string='Donor', required=True, ondelete='restrict',
        index=True)
    celebrant_id = fields.Many2one(
        'res.partner', string='Celebrant', domain=[('celebrant', '=', True)],
        ondelete='restrict', index=True,
        help="If the donor want the mass to be celebrated by a particular "
        "celebrant, select it here. Otherwise, leave empty.")
    donation_date = fields.Date(string='Donation Date', required=True)
    request_date = fields.Date(
        string='Celebration Requested Date',
        help="If the donor want the mass to be celebrated at a particular "
        "date, select it here. Otherwise, leave empty.")
    type_id = fields.Many2one(
        'mass.request.type', string='Mass Request Type', required=True,
        ondelete='restrict', readonly=True,
        states={'waiting': [('readonly', False)]})
    uninterrupted = fields.Boolean(
        related='type_id.uninterrupted', string="Uninterrupted", readonly=True)
    offering = fields.Monetary(
        string='Offering', currency_field='company_currency_id',
        readonly=True, states={'waiting': [('readonly', False)]},
        help="The total offering amount in company currency.")
    unit_offering = fields.Monetary(
        compute='_compute_unit_offering', store=True,
        string='Offering per Mass', currency_field='company_currency_id',
        help="This field is the offering amount per mass in company "
        "currency.")
    stock_account_id = fields.Many2one(
        'account.account', string='Stock Account',
        domain=[('deprecated', '!=', True)])
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Stock Analytic Account')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, ondelete='restrict',
        default=lambda self: self.env['res.company']._company_default_get(
            'mass.request'))
    company_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string="Company Currency", readonly=True)
    quantity = fields.Integer(
        'Quantity', default=1,
        readonly=True, states={'waiting': [('readonly', False)]})
    # quantity = quantity in the donation line
    mass_quantity = fields.Integer(
        compute='_compute_total_qty', string="Total Mass Quantity", store=True)
    intention = fields.Char(string='Intention')
    line_ids = fields.One2many(
        'mass.line', 'request_id', string='Mass Lines')
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('started', 'Started'),
        ('transfered', 'Transfered'),
        ('done', 'Done'),
        ], string='State', compute='_compute_state_mass_remaining_quantity',
        readonly=True, store=True)
    mass_remaining_quantity = fields.Integer(
        compute='_compute_state_mass_remaining_quantity',
        string="Mass Remaining Quantity", store=True)
    remaining_offering = fields.Monetary(
        compute='_compute_state_mass_remaining_quantity',
        string="Remaining Offering", store=True,
        currency_field='company_currency_id')
    transfer_id = fields.Many2one(
        'mass.request.transfer', string='Transfer Operation', readonly=True)

    def unlink(self):
        for request in self:
            if request.state != 'waiting':
                raise UserError(_(
                    'Cannot delete mass request dated %s for %s because '
                    'it is not in Waiting state.')
                    % (request.donation_date, request.partner_id.name))
        return super(MassRequest, self).unlink()


class MassLine(models.Model):
    _name = 'mass.line'
    _description = 'Mass Lines'
    _order = 'date desc, id desc'

    request_id = fields.Many2one(
        'mass.request', string='Mass Request',
        states={'done': [('readonly', True)]}, index=True)
    date = fields.Date(
        string='Celebration Date', required=True,
        states={'done': [('readonly', True)]})
    partner_id = fields.Many2one(
        'res.partner', related='request_id.partner_id', string="Donor",
        readonly=True, store=True)
    intention = fields.Char(
        related='request_id.intention', string="Intention",
        readonly=True)
    company_id = fields.Many2one(
        'res.company', related='request_id.company_id',
        string="Company", readonly=True, store=True)
    company_currency_id = fields.Many2one(
        'res.currency', related='request_id.company_id.currency_id',
        string="Company Currency", readonly=True)
    request_date = fields.Date(
        related='request_id.request_date', store=True,
        string="Mass Request Date", readonly=True)
    type_id = fields.Many2one(
        'mass.request.type', related='request_id.type_id',
        string="Mass Request Type", readonly=True, store=True)
    unit_offering = fields.Monetary(
        string='Offering', currency_field='company_currency_id',
        help="The offering amount is in company currency.",
        states={'done': [('readonly', True)]})
    celebrant_id = fields.Many2one(
        'res.partner', string='Celebrant', required=True, index=True,
        domain=[('celebrant', '=', True), ('supplier', '=', False)],
        ondelete='restrict', states={'done': [('readonly', True)]})
    conventual_id = fields.Many2one(
        'religious.community', string='Conventual', ondelete='restrict',
        index=True, states={'done': [('readonly', True)]})
    move_id = fields.Many2one(
        'account.move', string='Account Move', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ], string='State', default='draft', readonly=True)

    def unlink(self):
        # Get the last journal date
        mass_lines = self.search([], limit=1, order='date desc')
        assert mass_lines,\
            'We HAVE mass lines, at least the ones selected for deletion!'
        last_date = mass_lines[0].date
        for mass in self:
            if mass.state == 'done':
                raise UserError(_(
                    'Cannot delete mass line dated %s for %s because '
                    'it is in Done state.')
                    % (mass.date, mass.partner_id.name))
            if mass.type_id.uninterrupted and mass.date < last_date:
                raise UserError(_(
                    "Cannot delete mass dated %s for %s because it is a %s "
                    "which is an uninterrupted mass.")
                    % (mass.date, mass.partner_id.name, mass.type_id.name))
        return super(MassLine, self).unlink()


class MassRequestTransfer(models.Model):
    _name = 'mass.request.transfer'
    _description = 'Transfered Mass Requests'
    _rec_name = 'number'

    def name_get(self):
        res = []
        for trf in self:
            res.append((
                trf.id, u'%s %s (%s)'
                % (trf.celebrant_id.name, trf.transfer_date, trf.state)))
        return res

    @api.one
    @api.depends(
        'mass_request_ids', 'mass_request_ids.mass_quantity',
        'mass_request_ids.offering')
    def _compute_transfer_totals(self):
        amount_total = 0.0
        mass_total = 0
        for request in self.mass_request_ids:
            amount_total += request.offering
            mass_total += request.mass_quantity
        self.amount_total = amount_total
        self.mass_total = mass_total

    number = fields.Char(
        string='Transfer Number', readonly=True)
    celebrant_id = fields.Many2one(
        'res.partner', string='Celebrant', required=True, index=True,
        domain=[('celebrant', '=', True), ('supplier', '=', True)],
        states={'done': [('readonly', True)]}, ondelete='restrict')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, ondelete='restrict',
        states={'done': [('readonly', True)]},
        default=lambda self: self.env['res.company']._company_default_get(
            'mass.request.transfer'))
    company_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string="Company Currency", readonly=True)
    transfer_date = fields.Date(
        string='Transfer Date', required=True,
        states={'done': [('readonly', True)]},
        default=fields.Date.context_today)
    mass_request_ids = fields.One2many(
        'mass.request', 'transfer_id', string='Mass Requests',
        states={'done': [('readonly', True)]})
    move_id = fields.Many2one(
        'account.move', string='Account Move', readonly=True)
    amount_total = fields.Monetary(
        compute='_compute_transfer_totals', type="float",
        string="Amount Total", currency_field='company_currency_id',
        store=True)
    mass_total = fields.Integer(
        compute='_compute_transfer_totals', string="Total Mass Quantity",
        store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ], string='State', readonly=True, default='draft')

    @api.model
    def _prepare_mass_transfer_move(self, number):
        movelines = []
        stock_aml = {}  # key = account_id, value = amount
        for request in self.mass_request_ids:
            stock_account_id = request.stock_account_id.id or False
            if not stock_account_id:
                raise UserError(_(
                    'Missing stock account on mass request of %s')
                    % request.partner_id.name)
            if stock_account_id:
                if stock_account_id in stock_aml:
                    stock_aml[stock_account_id] += request.offering
                else:
                    stock_aml[stock_account_id] = request.offering

        name = _('Masses transfer %s') % number
        partner_id = self.celebrant_id.id
        for stock_account_id, stock_amount in stock_aml.iteritems():
            movelines.append((0, 0, {
                'name': name,
                'credit': 0,
                'debit': stock_amount,
                'account_id': stock_account_id,
                'partner_id': partner_id,
                }))

        # counter-part
        movelines.append(
            (0, 0, {
                'debit': 0,
                'credit': self.amount_total,
                'name': name,
                'account_id':
                self.celebrant_id.property_account_payable_id.id,
                'partner_id': partner_id,
                }))

        vals = {
            'journal_id': self.company_id.mass_validation_journal_id.id,
            # TODO Same journal as validation journal ?
            'date': self.transfer_date,
            'ref': number,
            'line_ids': movelines,
            }
        return vals

    @api.one
    def validate(self):
        if not self.mass_request_ids:
            raise UserError(_(
                'Cannot validate a Mass Request Transfer without '
                'Mass Requests.'))
        if not self.company_id.mass_validation_journal_id:
            raise UserError(_(
                "The 'Mass Validation Journal' is not set on company '%s'")
                % self.company_id.name)

        transfer_vals = {'state': 'done'}
        number = self.number
        if not number:
            number = self.env['ir.sequence'].next_by_code(
                'mass.request.transfer')
            transfer_vals['number'] = number

        # Create account move
        move_vals = self._prepare_mass_transfer_move(number)
        move = self.env['account.move'].create(move_vals)
        if self.company_id.mass_post_move:
            move.post()

        transfer_vals['move_id'] = move.id
        self.write(transfer_vals)
        return

    @api.one
    def back_to_draft(self):
        if self.move_id:
            self.move_id.button_cancel()
            self.move_id.unlink()
        self.state = 'draft'
        return

    def unlink(self):
        for trf in self:
            if trf.state == 'done':
                raise UserError(_(
                    'Cannot delete mass request transfer dated %s for %s '
                    'because it is Done state.')
                    % (trf.transfer_date, trf.celebrant_id.name))
        return super(MassRequestTransfer, self).unlink()
