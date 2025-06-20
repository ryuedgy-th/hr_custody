# Open HRMS Custody - Technical Guide

## Module Architecture

The Open HRMS Custody module is built on Odoo's standard framework with the following key components:

### Models

1. **hr.custody** (`models/hr_custody.py`): Main model for custody requests
2. **custody.property** (`models/custody_property.py`): Model for company properties
3. **custody.category** (`models/custody_category.py`): Model for property categories
4. **custody.tag** (`models/custody_tag.py`): Model for property tags
5. **custody.image** (`models/custody_image.py`): Model for multiple images
6. **hr.employee** (`models/hr_employee.py`): Extended employee model with custody-related fields

### Views

1. **hr_custody_views.xml**: Views for custody requests
2. **custody_property_views.xml**: Views for properties
3. **custody_category_views.xml**: Views for categories
4. **custody_tag_views.xml**: Views for tags
5. **custody_image_views.xml**: Views for images
6. **hr_employee_views.xml**: Extended employee views

### Wizards

1. **property_return_reason.py**: Wizard for providing return reason
2. **property_return_date.py**: Wizard for setting return date
3. **multi_images_upload.py**: Wizard for uploading multiple images

### Reports

1. **report_custody.py**: Report model for custody statistics
2. **report_custody_views.xml**: Report views

## Database Schema

### hr.custody

| Field Name | Type | Description |
|------------|------|-------------|
| name | Char | Unique code for custody record |
| employee_id | Many2one | Related employee |
| custody_property_id | Many2one | Property in custody |
| date_request | Date | Request date |
| purpose | Char | Reason for custody |
| return_type | Selection | Fixed date, flexible, or term-end |
| return_date | Date | Expected return date |
| expected_return_period | Char | Description for flexible return |
| state | Selection | Status (draft, to_approve, approved, returned, rejected) |
| image_ids | One2many | Related images |

### custody.property

| Field Name | Type | Description |
|------------|------|-------------|
| name | Char | Property name |
| property_code | Char | Unique identifier |
| category_id | Many2one | Property category |
| tag_ids | Many2many | Property tags |
| property_status | Selection | Status (available, in_use, etc.) |
| approver_ids | Many2many | Users who can approve requests |

## Key Workflows

### Custody Request Workflow

1. **Draft**: Initial state when created
2. **To Approve**: Sent for approval
3. **Approved**: Request approved, property assigned
4. **Returned**: Property returned
5. **Rejected**: Request refused

### Approval Process

1. Property-specific approvers are defined in the property record
2. When a request is sent for approval, approvers receive notification
3. Any designated approver can approve or reject the request
4. Approval records who approved and when

### Email Notifications

The module includes several email templates:

1. **mail_custody_notification_data.xml**: Contains templates for:
   - New custody request notification
   - Approval notification
   - Rejection notification
   - Return reminder notification

### Scheduled Actions

1. **ir_cron_data.xml**: Contains scheduled action for:
   - Daily check for upcoming returns to send reminders

## Extension Points

### Inheriting the Module

To extend this module, create a new module with a dependency on `hr_custody`:

```python
{
    'name': 'Extended HR Custody',
    'version': '18.0.1.0.0',
    'depends': ['hr_custody'],
    # ...
}
```

### Adding Custom Fields

Example of extending the custody model with custom fields:

```python
from odoo import fields, models

class HrCustodyExtended(models.Model):
    _inherit = 'hr.custody'
    
    custom_field = fields.Char(string='Custom Field')
```

### Adding Custom Approval Logic

Example of extending the approval method:

```python
from odoo import models

class HrCustodyExtended(models.Model):
    _inherit = 'hr.custody'
    
    def approve(self):
        # Custom logic before approval
        result = super(HrCustodyExtended, self).approve()
        # Custom logic after approval
        return result
```

## Common Issues and Solutions

### Issue: Property shows as available but can't be selected

**Solution**: Check if the property has approvers defined. Properties without approvers cannot be requested.

### Issue: Email notifications not sending

**Solution**: Verify the email server configuration in Odoo settings and check that the email templates are properly configured.

### Issue: Images not displaying correctly

**Solution**: Check image size and format. The module uses Odoo's image field with size limitations.

## Performance Considerations

1. **Image Handling**: Large images are automatically resized but can still impact performance
2. **Search Optimization**: The module uses custom name_search methods for better searching
3. **Computed Fields**: Several computed fields are stored for better performance 