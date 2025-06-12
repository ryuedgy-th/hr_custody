# Simple Asset Tracking for International Schools

## Why NOT use Stock Module for Schools:
❌ Complex inventory valuation (schools don't sell)
❌ Purchase/Sale workflows (not needed)
❌ Multi-warehouse complexity (usually single campus)
❌ Stock accounting overhead
❌ Vendor management (separate Purchase module exists)

## Recommended Approach: Custom Asset Tracking

### 1. Simple Barcode System
```python
class CustodyProperty(models.Model):
    _inherit = 'custody.property'
    
    # Simple asset tracking
    asset_tag = fields.Char('Asset Tag', required=True)
    qr_code = fields.Char('QR Code', compute='_compute_qr_code', store=True)
    barcode_image = fields.Binary('Barcode Image', compute='_compute_barcode_image')
    
    @api.depends('asset_tag')
    def _compute_qr_code(self):
        for record in self:
            record.qr_code = f"ASSET-{record.asset_tag}"
```

### 2. Simple Location Tracking
```python
class PropertyLocation(models.Model):
    _name = 'property.location'
    _description = 'Property Location'
    _parent_store = True
    
    name = fields.Char('Location Name', required=True)
    parent_id = fields.Many2one('property.location', 'Parent Location')
    location_type = fields.Selection([
        ('campus', 'Campus'),
        ('building', 'Building'), 
        ('floor', 'Floor'),
        ('room', 'Room')
    ], required=True)
    
class CustodyProperty(models.Model):
    _inherit = 'custody.property'
    
    current_location_id = fields.Many2one('property.location', 'Current Location')
    location_history_ids = fields.One2many('property.location.history', 'property_id')
```

### 3. Asset Registry (Government Required)
```python
class CustodyProperty(models.Model):
    _inherit = 'custody.property'
    
    # Government asset registry fields
    asset_number = fields.Char('Asset Number')  # หมายเลขครุภัณฑ์
    acquisition_date = fields.Date('Acquisition Date')
    acquisition_cost = fields.Monetary('Acquisition Cost')
    depreciation_rate = fields.Float('Depreciation Rate (%)')
    current_value = fields.Monetary('Current Value', compute='_compute_current_value')
    asset_classification = fields.Selection([
        ('building', 'Building & Infrastructure'),
        ('equipment', 'Equipment & Machinery'),
        ('vehicle', 'Vehicles'),
        ('furniture', 'Furniture & Fixtures'),
        ('it', 'IT Equipment'),
        ('educational', 'Educational Materials')
    ])
```

### 4. Maintenance Tracking
```python
class PropertyMaintenance(models.Model):
    _name = 'property.maintenance'
    _description = 'Property Maintenance Schedule'
    
    property_id = fields.Many2one('custody.property', required=True)
    maintenance_type = fields.Selection([
        ('preventive', 'Preventive'),
        ('corrective', 'Corrective'),
        ('calibration', 'Calibration')
    ])
    scheduled_date = fields.Date('Scheduled Date')
    completed_date = fields.Date('Completed Date')
    cost = fields.Monetary('Maintenance Cost')
    notes = fields.Text('Notes')
```

## Benefits for Schools:
✅ Simple to understand and use
✅ Focus on actual school needs
✅ Easy maintenance tracking
✅ Government compliance ready
✅ Cost tracking without complexity
✅ QR codes for quick access
✅ Location tracking
✅ No unnecessary inventory features

## Implementation Focus:
1. **Asset Lifecycle Management**
2. **Simple Check-in/Check-out**
3. **Maintenance Scheduling** 
4. **Government Reporting**
5. **Usage Analytics**
6. **Mobile-friendly QR scanning**
