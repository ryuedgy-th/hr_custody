    # ===== NEW: Multiple Image Upload Actions =====
    def action_upload_before_images(self):
        """Action to open multiple before images upload wizard"""
        self.ensure_one()
        if not self.can_take_before_photos:
            raise UserError(_('Before photos cannot be taken in current state: %s') %
                          dict(self._fields['state'].selection)[self.state])

        return {
            'name': _('📸 Upload Multiple Before Images'),
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_custody_id': self.id,
                'default_image_type': 'before',
            }
        }

    def action_upload_after_images(self):
        """Action to open multiple after images upload wizard"""
        self.ensure_one()
        if not self.can_take_after_photos:
            raise UserError(_('After photos cannot be taken in current state: %s') %
                          dict(self._fields['state'].selection)[self.state])

        return {
            'name': _('📸 Upload Multiple After Images'),
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_custody_id': self.id,
                'default_image_type': 'after',
            }
        }

    def action_upload_damage_images(self):
        """Action to open multiple damage images upload wizard"""
        self.ensure_one()
        if self.state not in ['approved', 'returned']:
            raise UserError(_('Damage photos can only be uploaded when custody is approved or returned'))

        return {
            'name': _('📸 Upload Multiple Damage Images'),
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_custody_id': self.id,
                'default_image_type': 'damage',
            }
        }