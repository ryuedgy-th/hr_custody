# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class PropertyReturnDate(models.TransientModel):
    """Hr custody contract renewal wizard"""
    _name = 'property.return.date'
    _description = 'Property Return Date'

    returned_date = fields.Date(
        string='Renewal Date',
        required=True,
        help='Add the Return date',
        default=fields.Date.today
    )

    custody_id = fields.Many2one(
        'hr.custody',
        string='Custody Record',
        help='Related custody record'
    )

    current_return_date = fields.Date(
        string='Current Return Date',
        readonly=True,
        help='Current return date of the custody'
    )

    employee_name = fields.Char(
        string='Employee',
        readonly=True,
        help='Employee name'
    )

    property_name = fields.Char(
        string='Property',
        readonly=True,
        help='Property name'
    )

    @api.model
    def default_get(self, fields_list):
        """Override default_get to populate custody information"""
        result = super(PropertyReturnDate, self).default_get(fields_list)

        custody_id = self.env.context.get('custody_id')
        if custody_id:
            custody_obj = self.env['hr.custody'].browse(custody_id)
            if custody_obj.exists():
                result.update({
                    'custody_id': custody_id,
                    'current_return_date': custody_obj.return_date,
                    'employee_name': custody_obj.employee_id.name,
                    'property_name': custody_obj.custody_property_id.name,
                })

        return result

    @api.constrains('returned_date')
    def validate_return_date(self):
        """The function used to renewal date validation"""
        for record in self:
            if record.custody_id:
                custody_obj = record.custody_id
                if record.returned_date <= custody_obj.date_request:
                    raise ValidationError(_('Renewal date must be after the request date (%s)') % custody_obj.date_request)

                if record.returned_date <= custody_obj.return_date:
                    raise ValidationError(_('Renewal date must be after the current return date (%s)') % custody_obj.return_date)
            else:
                # Fallback for context-based validation
                custody_id = self.env.context.get('custody_id')
                if custody_id:
                    custody_obj = self.env['hr.custody'].browse(custody_id)
                    if custody_obj.exists() and record.returned_date <= custody_obj.date_request:
                        raise ValidationError(_('Please Give Valid Renewal Date'))

    def proceed(self):
        """The function used to proceed
        with the renewal process for the associated custody."""
        custody_id = self.custody_id.id if self.custody_id else self.env.context.get('custody_id')

        if not custody_id:
            raise UserError(_('No custody record found'))

        custody_obj = self.env['hr.custody'].browse(custody_id)

        if not custody_obj.exists():
            raise UserError(_('Custody record not found'))

        if custody_obj.state != 'approved':
            raise UserError(_('Only approved custody records can be renewed'))

        # Update custody record
        custody_obj.write({
            'is_renew_return_date': True,
            'renew_date': self.returned_date,
            'state': 'to_approve'
        })

        # Post message for tracking
        custody_obj.message_post(
            body=_('Renewal requested with new return date: %s') % self.returned_date,
            message_type='notification'
        )

        return {
            'type': 'ir.actions.act_window_close',
            'infos': {
                'title': _('Success'),
                'message': _('Renewal request submitted successfully')
            }
        }

    def action_cancel(self):
        """Cancel the renewal process"""
        return {'type': 'ir.actions.act_window_close'}
