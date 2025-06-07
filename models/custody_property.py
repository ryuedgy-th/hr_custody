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
from odoo import api, fields, models, _


class CustodyProperty(models.Model):
    """
        Hr property creation model.
    """
    _name = 'custody.property'
    _description = 'Custody Property'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Property Name',
        required=True,
        help='Enter the name of the custody property'
    )

    image = fields.Image(
        string="Image",
        help="This field holds the image used for "
             "this provider, limited to 1024x1024px"
    )

    # Remove image_medium and image_small as they are deprecated in Odoo 18
    # Odoo 18 handles image resizing automatically with the Image field

    desc = fields.Html(
        string='Description',
        help='A detailed description of the item.'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        help='The company associated with this record.',
        default=lambda self: self.env.company
    )

    property_selection = fields.Selection([
        ('empty', 'No Connection'),
        ('product', 'Products')
    ],
        default='empty',
        string='Property From',
        help="Select the property"
    )

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        help="Select the Product"
    )

    # Computed fields for better tracking
    custody_count = fields.Integer(
        string='Active Custodies',
        compute='_compute_custody_count',
        help='Number of active custodies for this property'
    )

    is_available = fields.Boolean(
        string='Available',
        compute='_compute_is_available',
        help='Whether this property is available for custody'
    )

    @api.depends('product_id')
    def _onchange_product_id(self):
        """The function is used to
            change product Automatic
            fill name field"""
        for record in self:
            if record.product_id:
                record.name = record.product_id.name

    @api.depends('name')
    def _compute_custody_count(self):
        """Compute the number of active custodies for this property"""
        for record in self:
            custody_count = self.env['hr.custody'].search_count([
                ('custody_property_id', '=', record.id),
                ('state', '=', 'approved')
            ])
            record.custody_count = custody_count

    @api.depends('custody_count')
    def _compute_is_available(self):
        """Compute if the property is available for custody"""
        for record in self:
            record.is_available = record.custody_count == 0

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Override name_search to search in description as well"""
        if args is None:
            args = []

        if name:
            domain = ['|', ('name', operator, name), ('desc', operator, name)]
            records = self.search(domain + args, limit=limit)
            return records.name_get()

        return super(CustodyProperty, self).name_search(name, args, operator, limit)

    def name_get(self):
        """Override name_get to show availability status"""
        result = []
        for record in self:
            name = record.name
            if not record.is_available:
                name += _(' (In Use)')
            result.append((record.id, name))
        return result

    def action_view_custodies(self):
        """Action to view all custodies related to this property"""
        self.ensure_one()
        return {
            'name': _('Custodies for %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'hr.custody',
            'view_mode': 'list,form',
            'domain': [('custody_property_id', '=', self.id)],
            'context': {'default_custody_property_id': self.id}
        }
