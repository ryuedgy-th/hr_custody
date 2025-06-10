# Phase 1: Stock Integration Plan

## 1. Update Dependencies
Add 'stock' to depends in __manifest__.py

## 2. Extend Property Model
```python
class CustodyProperty(models.Model):
    _inherit = 'custody.property'
    
    # Link to product
    product_id = fields.Many2one('product.product', 'Related Product',
                                 domain=[('is_custody_property', '=', True)])
    
    # Stock tracking fields
    tracking = fields.Selection(related='product_id.tracking', readonly=True)
    lot_ids = fields.One2many('stock.lot', 'product_id', 'Serial Numbers/Lots')
    current_location_id = fields.Many2one('stock.location', 'Current Location')
    
    # Barcode from product
    barcode = fields.Char(related='product_id.barcode', readonly=True)
```

## 3. Extend Product Model
```python
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    is_custody_property = fields.Boolean('Is Custody Property')
    custody_property_ids = fields.One2many('custody.property', 'product_id', 
                                          'Custody Properties')

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    @api.model
    def create_custody_property(self, vals):
        # Auto-create custody property when product is flagged
        pass
```

## 4. Stock Location for Employees
```python
class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    stock_location_id = fields.Many2one('stock.location', 'Employee Location')
    
    @api.model
    def create(self, vals):
        # Auto-create employee location
        employee = super().create(vals)
        location = self.env['stock.location'].create({
            'name': f"Employee: {employee.name}",
            'usage': 'internal',
            'employee_id': employee.id
        })
        employee.stock_location_id = location.id
        return employee
```

## 5. Custody with Stock Moves
```python
class HrCustody(models.Model):
    _inherit = 'hr.custody'
    
    stock_move_ids = fields.One2many('stock.move', 'custody_id', 'Stock Moves')
    
    def action_approve(self):
        super().action_approve()
        # Create stock move: Warehouse → Employee Location
        self._create_stock_move()
    
    def action_return_approve(self):
        super().action_return_approve()
        # Create stock move: Employee Location → Warehouse
        self._create_return_stock_move()
```

## Benefits:
✅ Unified barcode system
✅ Real-time location tracking  
✅ Stock movement history
✅ Inventory reports integration
✅ Mobile barcode scanning
✅ RFID support (future)
