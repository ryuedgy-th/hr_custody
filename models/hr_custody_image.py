from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrCustodyImage(models.AbstractModel):
    """
    Image-related functionality for Hr Custody.
    """
    _name = 'hr.custody.image'
    _description = 'Hr Custody Image Mixin'

    # Image fields for documenting equipment condition
    checkout_image = fields.Image(
        string="Checkout Image",
        help="Image of the equipment when checked out to the employee",
        attachment=True,
        max_width=1920,
        max_height=1920,
        prefetch=False
    )
    
    checkout_image_date = fields.Datetime(
        string="Checkout Image Date",
        readonly=True,
        help="Date and time when the checkout image was captured"
    )
    
    checkout_condition_notes = fields.Text(
        string="Checkout Condition Notes",
        help="Notes about the condition of the equipment when checked out"
    )
    
    return_image = fields.Image(
        string="Return Image",
        help="Image of the equipment when returned by the employee",
        attachment=True,
        max_width=1920,
        max_height=1920,
        prefetch=False
    )
    
    return_image_date = fields.Datetime(
        string="Return Image Date",
        readonly=True,
        help="Date and time when the return image was captured"
    )
    
    return_condition_notes = fields.Text(
        string="Return Condition Notes",
        help="Notes about the condition of the equipment when returned"
    )

    # Multiple images feature
    image_ids = fields.One2many(
        'custody.image',
        'custody_id',
        string='Additional Images',
        help='Additional images for this custody record',
        prefetch=False,
        copy=False
    )
    
    checkout_image_count = fields.Integer(
        string='Checkout Images',
        compute='_compute_image_counts',
        help='Number of checkout images'
    )
    
    return_image_count = fields.Integer(
        string='Return Images',
        compute='_compute_image_counts',
        help='Number of return images'
    )

    @api.depends('image_ids')
    def _compute_image_counts(self):
        """Compute the number of images for each type"""
        for record in self:
            record.checkout_image_count = len(record.image_ids.filtered(lambda i: i.image_type == 'checkout'))
            record.return_image_count = len(record.image_ids.filtered(lambda i: i.image_type == 'return'))

    @api.onchange('checkout_image')
    def _onchange_checkout_image(self):
        """Update checkout image timestamp when image uploaded"""
        if self.checkout_image:
            self.checkout_image_date = fields.Datetime.now()
    
    @api.onchange('return_image')
    def _onchange_return_image(self):
        """Update return image timestamp when image uploaded"""
        if self.return_image:
            self.return_image_date = fields.Datetime.now()

    def action_view_image_comparison(self):
        """Open a wizard to compare checkout and return images side by side"""
        self.ensure_one()
        
        # Check if both types of images exist
        checkout_images = self.env['custody.image'].search([
            ('custody_id', '=', self.id),
            ('image_type', '=', 'checkout')
        ], limit=1)
        
        return_images = self.env['custody.image'].search([
            ('custody_id', '=', self.id),
            ('image_type', '=', 'return')
        ], limit=1)
        
        # If any image type is missing, show notification
        if not checkout_images or not return_images:
            missing = []
            if not checkout_images:
                missing.append("checkout")
            if not return_images:
                missing.append("return")
                
            raise UserError(_("Cannot compare images. Missing %s image(s). Please upload images first.") % (" and ".join(missing)))
        
        # Create context for opening comparison view
        context = self.env.context.copy()
        context.update({
            'default_checkout_images': checkout_images.ids,
            'default_return_images': return_images.ids,
            'no_breadcrumbs': True
        })
        
        # Open comparison view
        return {
            'name': _('Image Comparison - %s') % self.name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.custody',
            'res_id': self.id,
            'target': 'new',
            'view_id': self.env.ref('hr_custody.hr_custody_view_image_comparison').id,
            'context': context,
        }

    def action_view_images(self, image_type=None):
        """Open a view to manage images of a specific type or all images"""
        self.ensure_one()
        
        # Always strictly filter by custody_id to prevent mixing images
        domain = [('custody_id', '=', self.id)]
        context = {
            'default_custody_id': self.id,
            'search_default_custody_id': self.id,  # Ensure filtering by current custody
            'strict_custody_filter': self.id,  # Custom key to enforce strict filtering
            'no_breadcrumbs': True,
        }
        
        if image_type:
            # Add domain filter but keep it minimal for better performance
            domain.append(('image_type', '=', image_type))
            context['default_image_type'] = image_type
            context['search_default_' + image_type + '_images'] = 1  # Activate the relevant filter
            
            if image_type == 'checkout':
                title = _('Checkout Images - %s') % self.name
            elif image_type == 'return':
                title = _('Return Images - %s') % self.name
            else:
                title = _('Images - %s') % self.name
        else:
            title = _('All Images - %s') % self.name
        
        # Use a custodial ID in the key to ensure caching doesn't mix images
        view_key = f'custody_images_{self.id}_{image_type or "all"}'
            
        return {
            'name': title,
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image',
            'view_mode': 'kanban,form',
            'domain': domain,
            'context': context,
            'target': 'current',
            'key2': view_key,  # Use a unique key for this view
            'help': '<p class="o_view_nocontent_smiling_face">No images found</p><p>Upload images for this custody record.</p>'
        }
        
    def action_add_image(self, image_type=None):
        """Quick action to add a new image of a specific type"""
        self.ensure_one()
        
        context = {
            'default_custody_id': self.id,
        }
        
        if image_type:
            context['default_image_type'] = image_type
            
        return {
            'name': _('Add Image'),
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }

    def action_add_multiple_images(self):
        """Open wizard to upload multiple images at once"""
        self.ensure_one()
        
        action = self.env['ir.actions.act_window']._for_xml_id('hr_custody.action_custody_multi_images_upload')
        action['context'] = {
            'default_custody_id': self.id,
            'default_image_type': self.state == 'approved' and 'return' or 'checkout',
        }
        return action
        
    def action_manage_multiple_images(self):
        """Open list view to manage multiple images for this custody"""
        self.ensure_one()
        
        # Use list view first for multi-selection/deletion
        return {
            'name': _('Manage Images - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image',
            'view_mode': 'list,kanban,form',
            'domain': [('custody_id', '=', self.id)],
            'context': {
                'default_custody_id': self.id,
                'search_default_custody_id': self.id,
                'strict_custody_filter': self.id,
                'create': True,
                'edit': True,
                'delete': True
            },
            'help': '<p class="o_view_nocontent_smiling_face">No images found</p>'
                   '<p>You can select multiple images and delete them at once.</p>'
        }