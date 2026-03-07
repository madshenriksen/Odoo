# maintenance_equipment_from_serial

Custom Odoo module for linking Inventory serial numbers with Maintenance equipment.

## Purpose

This module extends the connection between:

- Inventory (`stock.lot`)
- Manufacturing (`mrp.production`, `mrp.bom`)
- Maintenance (`maintenance.equipment`)
- Repairs (`repair.order`)

It allows controlled creation of Maintenance Equipment from serial numbers and keeps related data synchronized.

## Main features

### Equipment creation from Lot/Serial
- Adds a **Create Equipment** button on Lot/Serial records
- Only visible when the product is marked as **Track as Equipment**
- Prevents duplicate equipment creation for the same serial

### Equipment data synchronization
When Equipment is created from a serial number, the module sets:

- **Name** from Lot reference (`stock.lot.ref`)
- **Serial Number** from Lot name (`stock.lot.name`)
- **Vendor** from current company
- **Vendor Reference** from Product Internal Reference (`product.default_code`)
- **Model** from BoM Reference (`mrp.bom.code`)
- **Equipment Category** from the Product configuration
- **Manufacturing Order** from the producing MO
- Link back to the originating Lot/Serial

### Product configuration
Products can be configured with:

- **Track as Equipment**
- **Equipment Category**

Only products marked as **Track as Equipment** can create equipment from serial numbers.

### Installed Components
Adds an **Installed Components** tab on Equipment showing the currently installed serialized components.

The list is initially populated from consumed serial-tracked components in Manufacturing Orders.

### Component History
Adds a **Component History** tab on Equipment showing component changes as events:

- Production events
- Repair events

Displayed columns include:

- Type
- Order
- Component
- Removed Serial
- Added Serial

### Repair integration
- Repair completion updates Installed Components automatically
- Repair history is stored as component events
- Existing repairs can be backfilled using the manual sync action

### Smart buttons
Adds or reuses smart buttons on Equipment for:

- Sales
- Transfers
- Location
- Traceability
- Repairs
- Installed Components

### Search and usability improvements
- Search Equipment by installed component serial number
- Group by Customer / Model / Category
- Optional columns in Equipment list view
- Customer shown from Lot/Serial last delivery partner
- "Used By", Department, and Employee fields removed from Equipment form

## Technical overview

### Main model extensions

#### `maintenance.equipment`
Extended with:
- `serial_lot_id`
- `product_id`
- `production_id`
- `production_name`
- `bom_id`
- installed components relations
- component history relations
- sync helpers

#### `stock.lot`
Extended with:
- equipment relations
- `track_as_equipment` related field
- equipment creation action
- where-used logic

#### `product.template`
Extended with:
- `track_as_equipment`
- `equipment_category_id`

#### New models
- `maintenance.equipment.component`
- `maintenance.equipment.component.event`

## Synchronization behavior

### Automatic sync
The module automatically synchronizes:

- Equipment serial/name from Lot/Serial
- Manufacturing Order from produced lot
- BoM on Equipment
- Installed Components from Manufacturing + Repairs
- Component History from Manufacturing + Repairs

### Manual sync
A manual action is available on Equipment to rebuild:

- Installed Components
- Component History
- Manufacturing / repair-derived state

This is useful for legacy data and troubleshooting.

## Dependencies

- `stock`
- `maintenance`
- `mrp`
- `sale_stock`
- `repair`

## Installation

1. Place the module in your Odoo custom addons path
2. Restart Odoo
3. Update Apps List
4. Install or upgrade the module

## Notes
This module is designed for serialized products and repair traceability workflows.
It is especially useful where equipment must reflect the real serialized configuration built in Manufacturing and changed through Repairs.

## Author
Custom implementation for internal use.
