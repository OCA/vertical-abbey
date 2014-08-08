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
from openerp.tools.translate import _


class mass_journal_validate(orm.TransientModel):
    _name = 'mass.journal.validate'
    _description = "Validate Masses Journal"

    _columns = {
        'journal_date': fields.date('Journal Date', required=True),
        }

    def _get_default_journal_date(self, cr, uid, context=None):
        line_id = self.pool['mass.line'].search(
            cr, uid, [('state', '=', 'draft')], limit=1,
            order='date asc', context=context)
        res = self.pool['mass.line'].browse(cr, uid, line_id, context=context)
        if res:
            default_str = res[0].date
        else:
            default_str = fields.date.context_today(
                self, cr, uid, context=context)
        return default_str

    _defaults = {
        'journal_date': _get_default_journal_date,
        }

    def _prepare_mass_validation_move(
            self, cr, uid, company, date, line_ids, context=None):
        if context is None:
            context = {}

        ctx_period = context.copy()
        ctx_period['account_period_prefer_normal'] = True
        period_search = self.pool['account.period'].find(
            cr, uid, date, context=ctx_period)
        assert len(period_search) == 1, 'We should get one period'
        period_id = period_search[0]

        movelines = []
        stock_aml = {}  # key = account_id, value = amount
        income_aml = {}
        # key = (account_id, analytic_account_id) value = amount
        income_account_id = company.mass_validation_account_id.id
        for line in self.pool['mass.line'].browse(
                cr, uid, line_ids, context=context):
            stock_account_id = line.request_id.stock_account_id.id or False
            analytic_account_id = \
                line.request_id.analytic_account_id.id or False

            if stock_account_id:
                if stock_account_id in stock_aml:
                    stock_aml[stock_account_id] += line.unit_offering
                else:
                    stock_aml[stock_account_id] = line.unit_offering

                if (income_account_id, analytic_account_id) in income_aml:
                    income_aml[(income_account_id, analytic_account_id)] +=\
                        line.unit_offering
                else:
                    income_aml[(income_account_id, analytic_account_id)] =\
                        line.unit_offering

        name = _('Masses celebrated on %s') % date
        for stock_account_id, stock_amount in stock_aml.iteritems():
            movelines.append((0, 0, {
                'name': name,
                'credit': 0,
                'debit': stock_amount,
                'account_id': stock_account_id,
                }))

        # counter-part
        for (income_account_id, analytic_account_id), income_amount in\
                income_aml.iteritems():

            movelines.append(
                (0, 0, {
                    'debit': 0,
                    'credit': income_amount,
                    'name': name,
                    'account_id': income_account_id,
                    'analytic_account_id': analytic_account_id,
                    }))

        vals = {
            'journal_id': company.mass_validation_journal_id.id,
            'date': date,
            'period_id': period_id,
            'ref': _('Masses'),
            'line_id': movelines,
            }
        return vals

    def validate_journal(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Only 1 ID in this wizard'
        if context is None:
            context = {}
        wizard = self.browse(cr, uid, ids[0], context=context)
        date = wizard.journal_date
        # Search user company
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        company = user.company_id
        company_id = user.company_id.id
        # Search draft mass lines on the date of the wizard
        line_ids = self.pool['mass.line'].search(
            cr, uid, [
                ('date', '=', date),
                ('company_id', '=', company_id)
                ], context=context)
        move_id = False
        if company.mass_validation_account_id:
            # Loop on result to compute the total amount
            if not company.mass_validation_journal_id:
                raise orm.except_orm(
                    _('Error:'),
                    _("Missing Mass Validation Journal on company '%s'.")
                    % company.name)
            # Create account move
            move_vals = self._prepare_mass_validation_move(
                cr, uid, company, date, line_ids, context=context)
            move_id = self.pool['account.move'].create(
                cr, uid, move_vals, context=context)

            self.pool['account.move'].post(cr, uid, [move_id], context=context)

        # Update mass lines
        self.pool['mass.line'].write(
            cr, uid, line_ids,
            {'state': 'done', 'move_id': move_id},
            context=context)

        action = {
            'name': _('Mass Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'mass.line',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', line_ids)],
            'nodestroy': False,
            'target': 'current',
            'context': {'mass_line_main_view': True},
            }
        return action
