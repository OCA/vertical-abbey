# -*- encoding: utf-8 -*-
##############################################################################
#
#    Mass module for OpenERP
#    Copyright (C) 2014 Artisanat Monastique de Provence
#                  (http://www.barroux.org)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class res_partner(orm.Model):
    _inherit = "res.partner"

    _columns = {
        'celebrant': fields.boolean('Celebrant'),
        # A celebrant to which we transfer mass is celebrant + supplier
        }


class mass_request_type(orm.Model):
    _name = "mass.request.type"
    _description = 'Types of Mass Requests'
    _order = 'name'

    _columns = {
        'name': fields.char('Mass Request Type', size=128, required=True),
        'code': fields.char('Mass Request Code', size=5),
        'quantity': fields.integer('Quantity'),
        'uninterrupted': fields.boolean('Uninterrupted'),
        # True for Novena and Gregorian series ; False for others
    }


class product_template(orm.Model):
    _inherit = "product.template"

    _columns = {
        'mass': fields.boolean('Is a Mass'),
        'mass_request_type_id': fields.many2one(
            'mass.request.type', 'Mass Request Type'),
        }

    def mass_change(self, cr, uid, ids, mass, context=None):
        res = {'value': {}}
        if mass:
            res['value'] = {'type': 'service', 'sale_ok': False}
        return res


class product_product(orm.Model):
    _inherit = 'product.product'

    def mass_change(self, cr, uid, ids, mass, context=None):
        return self.pool['product.template'].mass_change(
            cr, uid, [], mass, context=context)


class religious_community(orm.Model):
    _name = "religious.community"
    _description = "Religious Community"

    _columns = {
        'name': fields.char('Community Code', size=12, required=True),
        'long_name': fields.char('Community Name', size=128),
        'active': fields.boolean('Active'),
        }

    _defaults = {
        'active': True,
    }


class mass_request(orm.Model):
    _name = 'mass.request'
    _description = 'Mass Request'
    _order = 'id desc'

    def _compute_request_properties(
            self, cr, uid, ids, name, arg, context=None):
        res = {}
        for request in self.browse(cr, uid, ids, context=context):
            total_qty = request.type_id.quantity * request.quantity
            remaining_qty = total_qty
            for line in request.line_ids:
                remaining_qty -= 1
            state = 'waiting'
            if request.transfer_id:
                state = 'transfered'
                remaining_qty = 0
            else:
                if remaining_qty < total_qty and request.uninterrupted:
                    state = 'started'
                if remaining_qty == 0:
                    state = 'done'
            if total_qty:
                unit_offering = request.offering / total_qty
            else:
                unit_offering = 0
            res[request.id] = {
                'mass_remaining_quantity': remaining_qty,
                'mass_quantity': total_qty,
                'unit_offering': unit_offering,
                'state': state,
                }
        return res

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for request in self.browse(cr, uid, ids, context=context):
            res.append((
                request.id,
                u'[%dx%s] %s' % (
                    request.quantity,
                    request.type_id.code,
                    request.partner_id.name,
                    )))
        return res

    def _get_mass_req_from_lines(self, cr, uid, ids, context=None):
        return self.pool['mass.request'].search(
            cr, uid, [('line_ids', 'in', ids)], context=context)

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Donor', required=True),
        'celebrant_id': fields.many2one(
            'res.partner', 'Celebrant', domain=[('celebrant', '=', True)]),
        'donation_date': fields.date('Donation Date', required=True),
        'request_date': fields.date('Mass Request Date'),
        'type_id': fields.many2one(
            'mass.request.type', 'Mass Request Type', required=True),
        'uninterrupted': fields.related(
            'type_id', 'uninterrupted', type="boolean",
            string="Uninterrupted"),
        'offering': fields.float(
            'Offering', digits_compute=dp.get_precision('Account'),
            help="The total offering amount in company currency."),
        'unit_offering': fields.function(
            _compute_request_properties, type="float",
            string='Offering per Mass', multi='mass_req',
            digits_compute=dp.get_precision('Account'),
            help="This field is the offering amount per mass in company "
            "currency."),
        'stock_account_id': fields.many2one(
            'account.account', 'Stock Account',
            domain=[('type', '<>', 'view'), ('type', '<>', 'closed')]),
        'analytic_account_id': fields.many2one(
            'account.analytic.account', 'Analytic Account',
            domain=[('type', 'not in', ('view', 'template'))]),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True),
        'company_currency_id': fields.related(
            'company_id', 'currency_id', type="many2one",
            relation='res.currency', string="Company Currency"),
        'quantity': fields.integer('Quantity'),
        # quantity = quantity in the donation line
        'mass_quantity': fields.function(
            _compute_request_properties, type="integer",
            string="Total Mass Quantity", multi='mass_req',
            store={
                'mass.request': (
                    lambda self, cr, uid, ids, c={}:
                    ids, ['quantity', 'type_id'], 10)
            }),
        'intention': fields.char('Intention', size=256),
        'line_ids': fields.one2many(
            'mass.line', 'request_id', 'Mass Lines'),
        'state': fields.function(
            _compute_request_properties, type="selection",
            selection=[
                ('waiting', 'Waiting'),
                ('started', 'Started'),
                ('transfered', 'Transfered'),
                ('done', 'Done'),
                ], string='State', readonly=True, multi='mass_req', store={
                'mass.request': (
                    lambda self, cr, uid, ids, c={}:
                    ids, ['transfer_id', 'quantity', 'type_id'], 10),
                'mass.line': (_get_mass_req_from_lines, ['request_id'], 20),
                    }),
        'mass_remaining_quantity': fields.function(
            _compute_request_properties, type="integer", multi='mass_req',
            string="Mass Remaining Quantity", store={
                'mass.request': (
                    lambda self, cr, uid, ids, c={}:
                    ids, ['transfer_id', 'quantity', 'type_id'], 10),
                'mass.line': (_get_mass_req_from_lines, ['request_id'], 20),
                }),
        'transfer_id': fields.many2one(
            'mass.request.transfer', 'Transfer Operation', readonly=True),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, context:
        self.pool['res.company']._company_default_get(
            cr, uid, 'mass.request', context=context),
        'quantity': 1,
        }


class mass_line(orm.Model):
    _name = 'mass.line'
    _description = 'Mass Lines'
    _order = 'date desc, id desc'

    _columns = {
        'request_id': fields.many2one('mass.request', 'Mass Request'),
        'date': fields.date('Celebration Date', required=True),
        'partner_id': fields.related(
            'request_id', 'partner_id', string="Donor", readonly=True,
            type="many2one", relation="res.partner"),
        'intention': fields.related(
            'request_id', 'intention', type="char", string="Intention",
            readonly=True),
        'company_id': fields.related(
            'request_id', 'company_id', type="many2one",
            relation="res.company", string="Company", readonly=True),
        'company_currency_id': fields.related(
            'company_id', 'currency_id', type="many2one",
            relation='res.currency', string="Company Currency"),
        'request_date': fields.related(
            'request_id', 'request_date', type="date",
            string="Mass Request Date", readonly=True),
        'type_id': fields.related(
            'request_id', 'type_id', type="many2one",
            relation="mass.request.type", string="Mass Request Type",
            readonly=True),
        'unit_offering': fields.float(
            'Offering', digits_compute=dp.get_precision('Account'),
            help="The offering amount is in company currency."),
        'celebrant_id': fields.many2one(
            'res.partner', 'Celebrant', required=True,
            domain=[('celebrant', '=', True), ('supplier', '=', False)]),
        'conventual_id': fields.many2one(
            'religious.community', 'Conventual'),
        'move_id': fields.many2one(
            'account.move', 'Account Move', readonly=True),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('done', 'Done'),
            ], 'State', readonly=True),
        }

    _defaults = {
        'state': 'draft',
        }

    def unlink(self, cr, uid, ids, context=None):
        # Get the last journal date
        line_id = self.search(
            cr, uid, [], limit=1, order='date desc', context=context)
        res = self.browse(cr, uid, line_id, context=context)
        if res:
            last_date = res[0].date
        else:
            raise orm.except_orm(
                _('Error:'),
                _("Empty journal."))                                     
        for mass in self.browse(cr, uid, ids, context=context):
            if mass.type_id.uninterrupted and mass.date < last_date:
                raise orm.except_orm(
                    _('Error:'),
                    _("Cannot delete mass dated %s for %s because it is a %s "
                        "which is an uninterrupted mass.")
                    % (mass.date, mass.partner_id.name, mass.type_id.name))
            if mass.state == 'done':
                raise orm.except_orm(
                    _('Error:'),
                    _('Cannot delete mass line dated %s for %s because '
                        'it is in Done state.')
                    % (mass.date, mass.partner_id.name))
        return super(mass_line, self).unlink(cr, uid, ids, context=context)


class mass_request_transfer(orm.Model):
    _name = 'mass.request.transfer'
    _description = 'Transfered Mass Requests'
    _rec_name = 'number'

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for trf in self.browse(cr, uid, ids, context=context):
            res.append((
                trf.id, u'%s (%s)'
                % (trf.celebrant_id.name, trf.transfer_date)))
        return res

    def _compute_transfer_totals(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for transfer in self.browse(cr, uid, ids, context=context):
            res[transfer.id] = {
                'amount_total': 0.0,
                'mass_total': 0,
                }
            for request in transfer.mass_request_ids:
                res[transfer.id]['amount_total'] += request.offering
                res[transfer.id]['mass_total'] += request.mass_quantity
        return res

    def _get_transfers_from_requests(self, cr, uid, ids, context=None):
        return self.pool['mass.request.transfer'].search(
            cr, uid, [('mass_request_ids', 'in', ids)], context=context)

    _columns = {
        'number': fields.char(
            'Transfer Number', size=32, readonly=True),
        'celebrant_id': fields.many2one(
            'res.partner', 'Celebrant', required=True,
            domain=[('celebrant', '=', True), ('supplier', '=', True)],
            states={'done': [('readonly', True)]}),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True,
            states={'done': [('readonly', True)]}),
        'company_currency_id': fields.related(
            'company_id', 'currency_id', type="many2one",
            relation='res.currency', string="Company Currency"),
        'transfer_date': fields.date(
            'Transfer Date', required=True,
            states={'done': [('readonly', True)]}),
        'mass_request_ids': fields.one2many(
            'mass.request', 'transfer_id', 'Mass Requests',
            states={'done': [('readonly', True)]}),
        'move_id': fields.many2one(
            'account.move', 'Account Move', readonly=True),
        'amount_total': fields.function(
            _compute_transfer_totals, type="float", string="Amount Total",
            digits_compute=dp.get_precision('Account'), multi="transfer",
            store={
                'mass.request': (
                    _get_transfers_from_requests,
                    ['transfer_id', 'mass_quantity', 'offering'], 10),
                }),
        'mass_total': fields.function(
            _compute_transfer_totals, type="integer",
            string="Total Mass Quantity", multi="transfer", store={
                'mass.request': (
                    _get_transfers_from_requests,
                    ['transfer_id', 'mass_quantity', 'offering'], 10),
                }),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('done', 'Done'),
            ], 'State', readonly=True),
        }

    _defaults = {
        'state': 'draft',
        'transfer_date': fields.date.context_today,
        'company_id': lambda self, cr, uid, context:
        self.pool['res.company']._company_default_get(
            cr, uid, 'mass.request.transfer', context=context),
        }

    def _prepare_mass_transfer_move(
            self, cr, uid, transfer, number, context=None):
        if context is None:
            context = {}
        ctx_period = context.copy()
        ctx_period['account_period_prefer_normal'] = True
        period_search = self.pool['account.period'].find(
            cr, uid, transfer.transfer_date, context=ctx_period)
        assert len(period_search) == 1, 'We should get one period'
        period_id = period_search[0]

        movelines = []
        stock_aml = {}  # key = account_id, value = amount
        for request in transfer.mass_request_ids:
            stock_account_id = request.stock_account_id.id or False
            if stock_account_id:
                if stock_account_id in stock_aml:
                    stock_aml[stock_account_id] += request.offering
                else:
                    stock_aml[stock_account_id] = request.offering

        print "stock_aml=", stock_aml
        name = _('Masses transfer %s') % number
        # TODO : move partner to parent ?
        partner_id = transfer.celebrant_id.id
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
                'credit': transfer.amount_total,
                'name': name,
                'account_id':
                transfer.celebrant_id.property_account_payable.id,
                'partner_id': partner_id,
                }))

        vals = {
            'journal_id': transfer.company_id.mass_validation_journal_id.id,
            # TODO Same journal as validation journal ?
            'date': transfer.transfer_date,
            'period_id': period_id,
            'ref': number,
            'line_id': movelines,
            }
        return vals

    def validate(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Only 1 ID for transfer validation'
        transfer = self.browse(cr, uid, ids[0], context=context)
        if not transfer.mass_request_ids:
            raise orm.except_orm(
                _('Error:'),
                _('Cannot validate a Mass Request Transfer without '
                    'Mass Requests.'))
        if not transfer.company_id.mass_validation_journal_id:
            raise orm.except_orm(
                _('Error:'),
                _("The 'Mass Validation Journal' is not set on company '%s'")
                % transfer.company_id.name)

        transfer_vals = {'state': 'done'}
        number = transfer.number
        if not number:
            number = self.pool['ir.sequence'].next_by_code(
                cr, uid, 'mass.request.transfer', context=context)
            transfer_vals['number'] = number

        # Create and post account move
        move_vals = self._prepare_mass_transfer_move(
            cr, uid, transfer, number, context=context)
        move_id = self.pool['account.move'].create(
            cr, uid, move_vals, context=context)
        self.pool['account.move'].post(cr, uid, [move_id], context=context)

        transfer_vals['move_id'] = move_id
        transfer.write(transfer_vals)
        return True

    def back_to_draft(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Only 1 ID accepted here'
        transfer = self.browse(cr, uid, ids[0], context=context)
        if transfer.move_id:
            self.pool['account.move'].button_cancel(
                cr, uid, [transfer.move_id.id], context=context)
            self.pool['account.move'].unlink(
                cr, uid, transfer.move_id.id, context=context)
        transfer.write({'state': 'draft'})
        return True
