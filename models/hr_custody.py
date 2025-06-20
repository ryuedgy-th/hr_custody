from odoo import api, fields, models, _


class HrCustody(models.Model):
    """
    Hr custody contract creation model.
    
    This model inherits from multiple mixins to organize functionality:
    - hr.custody.base: Core fields and basic functionality
    - hr.custody.approval: Approval-related methods
    - hr.custody.image: Image management functionality
    """
    _name = 'hr.custody'
    _description = 'Hr Custody Management'
    _inherit = [
        'mail.thread', 
        'mail.activity.mixin',
        'hr.custody.base',
        'hr.custody.approval', 
        'hr.custody.image'
    ]
    _order = 'date_request desc'
    _rec_name = 'name'

    @api.model_create_multi
    def create(self, vals_list):
        """Create a new record for the HrCustody model.
        
        This method is responsible for creating a new record for the HrCustody model
        with the provided values. It automatically generates a unique name for
        the record using the 'ir.sequence' and assigns it to the 'name' field.
        """
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.custody') or 'New'
        return super(HrCustody, self).create(vals_list)

    def set_to_return(self):
        """Override to add image handling when returning equipment"""
        # Update return image date if image exists but date not set
        if self.return_image and not self.return_image_date:
            self.return_image_date = fields.Datetime.now()
            
        # Call parent method which handles property status and basic return logic
        result = super(HrCustody, self).set_to_return()
        
        # Add condition notes to return message if provided
        if self.return_condition_notes:
            self.message_post(
                body=_('Return condition notes: %s') % self.return_condition_notes,
                message_type='notification'
            )
            
        return result

    def approve(self):
        """Override to add image handling when approving requests"""
        # Update checkout image date if image exists but date not set
        for record in self:
            if record.checkout_image and not record.checkout_image_date:
                record.checkout_image_date = fields.Datetime.now()
        
        # Call parent approval method
        return super(HrCustody, self).approve()