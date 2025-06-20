# Open HRMS Custody - Developer Guide

## Code Structure

The module follows the standard Odoo structure:

```
hr_custody/
  ├── __init__.py               # Module initialization
  ├── __manifest__.py           # Module manifest
  ├── data/                     # Data files
  ├── models/                   # Model definitions
  ├── security/                 # Access rights and rules
  ├── static/                   # Static assets
  ├── views/                    # View definitions
  ├── wizard/                   # Wizard models and views
  └── reports/                  # Report models and templates
```

## Key Models

### hr.custody

The main model for custody requests:

```python
class HrCustody(models.Model):
    _name = 'hr.custody'
    _description = 'Hr Custody Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_request desc'
    _rec_name = 'name'
    
    # Fields definition
    name = fields.Char(string='Code', readonly=True, copy=False)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    custody_property_id = fields.Many2one('custody.property', string='Property', required=True)
    # ... other fields
```

### custody.property

Model for company property:

```python
class CustodyProperty(models.Model):
    _name = 'custody.property'
    _description = 'Custody Property'
    _order = 'name'
    _rec_name = 'name'
    
    # Fields definition
    name = fields.Char(string='Property Name', required=True)
    property_code = fields.Char(string='Property Code')
    # ... other fields
```

## Workflows

### Custody Request Workflow

The custody request workflow is implemented through state changes:

1. **Draft**: Initial state
   ```python
   state = fields.Selection([
       ('draft', 'Draft'),
       ('to_approve', 'Waiting For Approval'),
       ('approved', 'Approved'),
       ('returned', 'Returned'),
       ('rejected', 'Refused')
   ], string='Status', default='draft')
   ```

2. **Send for Approval**: Changes state to 'to_approve'
   ```python
   def sent(self):
       self.state = 'to_approve'
       # Send notification to approvers
   ```

3. **Approve/Reject**: Changes state to 'approved' or 'rejected'
   ```python
   def approve(self):
       self.write({
           'state': 'approved',
           'approved_by_id': self.env.user.id,
           'approved_date': fields.Datetime.now(),
       })
       # Update property status and send notification
   ```

4. **Return**: Changes state to 'returned'
   ```python
   def set_to_return(self):
       self.state = 'returned'
       # Update property status and send notification
   ```

## Extending the Module

### Adding New Fields

To add new fields to existing models:

```python
from odoo import fields, models

class HrCustodyExtended(models.Model):
    _inherit = 'hr.custody'
    
    new_field = fields.Char(string='New Field')
```

### Adding New States

To add new states to the workflow:

```python
from odoo import fields, models

class HrCustodyExtended(models.Model):
    _inherit = 'hr.custody'
    
    state = fields.Selection(selection_add=[
        ('new_state', 'New State')
    ])
    
    def action_new_state(self):
        self.state = 'new_state'
```

### Adding New Approval Types

To add new approval types:

```python
from odoo import fields, models

class CustodyPropertyExtended(models.Model):
    _inherit = 'custody.property'
    
    secondary_approver_ids = fields.Many2many(
        'res.users',
        'custody_property_secondary_approver_rel',
        'property_id',
        'user_id',
        string='Secondary Approvers'
    )
```

## API Usage

### Creating a Custody Request

```python
# Create a custody request programmatically
custody_obj = self.env['hr.custody']
custody_id = custody_obj.create({
    'employee_id': employee.id,
    'custody_property_id': property.id,
    'purpose': 'For project work',
    'date_request': fields.Date.today(),
    'return_type': 'date',
    'return_date': fields.Date.today() + timedelta(days=30),
})

# Send for approval
custody_id.sent()
```

### Approving a Request

```python
# Approve a custody request programmatically
custody_id.approve()
```

### Returning a Property

```python
# Return a property programmatically
custody_id.set_to_return()
```

## Security Considerations

### Access Rights

The module defines the following access rights:

1. **Custody User**: Can create and view custody requests
2. **Custody Manager**: Can approve, reject, and manage all custody requests
3. **Property Manager**: Can create and manage property records

### Record Rules

Record rules restrict access based on user roles:

1. **Employee Rule**: Users can only see their own custody records
2. **Manager Rule**: Managers can see all custody records
3. **Approver Rule**: Approvers can see custody records they are assigned to approve

## Testing

### Test Cases

Key test cases to implement:

1. **Test Custody Creation**: Test creating a custody request
2. **Test Approval Process**: Test the approval workflow
3. **Test Return Process**: Test the property return process
4. **Test Email Notifications**: Test that email notifications are sent correctly

### Example Test

```python
from odoo.tests.common import TransactionCase

class TestHrCustody(TransactionCase):
    def setUp(self):
        super(TestHrCustody, self).setUp()
        # Setup test data
        
    def test_custody_creation(self):
        # Test creating a custody request
        custody = self.env['hr.custody'].create({
            'employee_id': self.employee.id,
            'custody_property_id': self.property.id,
            'purpose': 'Test purpose',
            'date_request': fields.Date.today(),
            'return_type': 'date',
            'return_date': fields.Date.today() + timedelta(days=10),
        })
        self.assertEqual(custody.state, 'draft')
        
    def test_custody_approval(self):
        # Test custody approval process
        custody = self.create_test_custody()
        custody.sent()
        self.assertEqual(custody.state, 'to_approve')
        custody.approve()
        self.assertEqual(custody.state, 'approved')
```

## Common Issues

### Issue: Sequence Generation

If the sequence for custody code is not generating correctly:

1. Check the `custody_sequence_data.xml` file
2. Verify the sequence is properly defined
3. Check that the sequence is being called in the `create` method

### Issue: Image Storage

If images are not being stored or displayed correctly:

1. Check that the image fields are defined with proper parameters
2. Verify that the image upload widgets are correctly configured in views
3. Check for image size limitations

## Performance Optimization

1. **Image Handling**: Use `max_width` and `max_height` parameters to limit image size
2. **Search Optimization**: Use indexes on frequently searched fields
3. **Computed Fields**: Store computed fields that are frequently accessed 