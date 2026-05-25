This JavaScript file patches the Odoo backend UI to:
- show the module icon near the favourite/star field in list and kanban records when published_stock_number is true
- ask for confirmation when saving a product.template with published_stock_number enabled

Depending on the exact Odoo 18 build/theme and product views in your database, selectors may need small adjustments.
