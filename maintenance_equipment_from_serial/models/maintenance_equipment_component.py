from odoo import models, fields, api


class MaintenanceEquipmentComponent(models.Model):
    _name = 'maintenance.equipment.component'
    _description = 'Installed Equipment Component'
    _order = 'product_name_sort, default_code, id'

    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Equipment',
        required=True,
        ondelete='cascade',
    )

    lot_id = fields.Many2one(
        'stock.lot',
        string='Serial Number',
        required=True,
        ondelete='restrict',
    )

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        related='lot_id.product_id',
        store=True,
        readonly=True,
    )
    
    product_name = fields.Char(
        string="Product",
        compute="_compute_product_name",
        store=True,
        translate=False,
    )

    product_name_sort = fields.Char(
        string="Product Sort",
        compute="_compute_product_name",
        store=True,
        translate=False,
    )

    @api.depends('product_id')
    def _compute_product_name(self):
        for rec in self:
            name = rec.product_id.with_context(lang=False).name or ''
            rec.product_name = name
            rec.product_name_sort = name

    default_code = fields.Char(
        string='Reference',
        related='product_id.default_code',
        store=True,
        readonly=True,
    )

    active_component = fields.Boolean(
        string='Currently Installed',
        default=True,
    )

    note = fields.Char(
        string='Note',

    )
