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
from odoo.exceptions import UserError


class PropertyReturnReason(models.TransientModel):
    """
        Hr custody contract refuse wizard.
    """
    _name = 'property.return.reason'
    _description = 'Property Return Reason'

    reason = fields.Text(
        string="Reason",
        required=True,
        help="Add the reason for rejection"
    )

    def send_reason(self):
        """The function used to send
        rejection reason for the associated record."""
        context = self.env.context
        model_id = context.get('model_id')
        reject_id = context.get('reject_id')

        if not model_id or not reject_id:
            raise UserError(_('Missing required context parameters'))

        # Get the record to be rejected
        reject_obj = self.env[model_id].browse(reject_id)

        if not reject_obj.exists():
            raise UserError(_('Record not found'))

        # Handle renewal rejection
        if 'renew' in context:
            reject_obj.write({
                'state': 'approved',
                'is_renew_reject': True,
                'renew_rejected_reason': self.reason
            })
            # Post message for tracking
            reject_obj.message_post(
                body=_('Renewal request rejected: %s') % self.reason,
                message_type='notification'
            )
        else:
            # Handle regular rejection
            if model_id == 'hr.holidays':
                # Special handling for hr.holidays if needed
                reject_obj.write({'rejected_reason': self.reason})
                reject_obj.action_refuse()
            else:
                # Standard custody rejection
                reject_obj.write({
                    'state': 'rejected',
                    'rejected_reason': self.reason
                })
                # Post message for tracking
                reject_obj.message_post(
                    body=_('Request rejected: %s') % self.reason,
                    message_type='notification'
                )

        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def default_get(self, fields_list):
        """Override default_get to set default values based on context"""
        result = super(PropertyReturnReason, self).default_get(fields_list)

        context = self.env.context
        if 'renew' in context:
            result['reason'] = _('Renewal request rejected')

        return result
