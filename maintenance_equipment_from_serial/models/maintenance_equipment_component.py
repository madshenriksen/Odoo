from odoo import models, fields


class MaintenanceEquipmentComponent(models.Model):
    _name = 'maintenance.equipment.component'
    _description = 'Installed Equipment Component'
    _order = 'id desc'

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
        related='product_id.name',
        store=True,
        readonly=True,
    )

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