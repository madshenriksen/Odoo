# Published Stock Number for Odoo 18

Adds a visual warning system for protected/public product numbers in Odoo Inventory.

This module introduces a new checkbox called **Published Stock Number** on products and visually highlights these products throughout the Inventory interface.

Designed for companies where certain stock numbers/product references are publicly published and should only be modified with extra caution.

---

## Features

### Product Flag

Adds a new checkbox on the product form:

- **Published Stock Number**

---

### Visual Highlighting

When enabled, a custom icon is displayed next to the product name in:

- Product Form View
- Product List View
- Product Kanban View

Different icon sizes are automatically used depending on the view.

---

### Save Confirmation Warning

When editing a product marked as **Published Stock Number**, a confirmation dialog appears before saving:

> "You are about to edit a Published Stock Number. Are you sure you want to proceed?"

Options:

- **OK** → Continue saving
- **Discard** → Cancel changes

The warning also appears if the checkbox itself is being removed.

---

## Installation

1. Copy the module into your custom addons directory.

2. Restart Odoo.

3. Update app list.

4. Install the module:
   - `Published Stock Number`

---

## Configuration

Replace the placeholder icon with your own PNG file:

```text
static/src/img/published_stock_number.png
```

Recommended:
- Transparent PNG
- Square format
- Around 32x32 or 64x64 px

---

## Technical Notes

### Model

Extends:

- `product.template`

Adds field:

```python
published_stock_number = fields.Boolean()
```

---

### Frontend

Uses OWL patches for:

- `ListRenderer`
- `KanbanRecord`
- `FormController`

---

### Assets

Includes:

- Custom JS
- Custom CSS
- Custom PNG icon

---

## Compatibility

Tested on:

- Odoo 18

May work on later versions with minor adjustments.

---

## License

LGPL-3