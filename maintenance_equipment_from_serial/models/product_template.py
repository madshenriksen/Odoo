from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    track_as_equipment = fields.Boolean(
        string="Track as Equipment",
        help="If enabled, serial numbers of this product can create Maintenance Equipment.",
    )

    equipment_category_id = fields.Many2one(
        'maintenance.equipment.category',
        string="Equipment Category",
    )