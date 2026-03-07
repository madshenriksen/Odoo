from odoo import models, fields


class MaintenanceEquipmentComponentEvent(models.Model):
    _name = 'maintenance.equipment.component.event'
    _description = 'Equipment Component History Event'
    _order = 'id desc'

    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Equipment',
        required=True,
        ondelete='cascade',
    )

    source_ref = fields.Reference(
        selection=[
            ('mrp.production', 'Production Order'),
            ('repair.order', 'Repair Order'),
        ],
        string='Order',
        readonly=True,
    )

    source_model = fields.Char(
        string='Source Model',
        readonly=True,
    )

    source_name = fields.Char(
        string='Order',
        readonly=True,
    )

    source_type = fields.Char(
        string="Type",
        compute="_compute_source_type",
    )

    product_id = fields.Many2one(
        'product.product',
        string='Component',
        readonly=True,
    )

    removed_lot_id = fields.Many2one(
        'stock.lot',
        string='Removed Serial',
        readonly=True,
    )

    added_lot_id = fields.Many2one(
        'stock.lot',
        string='Added Serial',
        readonly=True,
    )

    def _compute_source_type(self):
        for rec in self:
            if rec.source_model == 'mrp.production':
                rec.source_type = "Production"
            elif rec.source_model == 'repair.order':
                rec.source_type = "Repair"
            else:
                rec.source_type = "Manual"