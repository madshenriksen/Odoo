from odoo import models, fields, _
from odoo.exceptions import UserError


class StockLot(models.Model):
    _inherit = 'stock.lot'

    equipment_ids = fields.One2many(
        'maintenance.equipment',
        'serial_lot_id',
        string="Equipment",
    )

    equipment_count = fields.Integer(
        string="Equipment Count",
        compute="_compute_equipment_count",
    )

    track_as_equipment = fields.Boolean(
        string="Track as Equipment",
        related='product_id.product_tmpl_id.track_as_equipment',
        readonly=True,
    )

    where_used_equipment_id = fields.Many2one(
        'maintenance.equipment',
        string="Installed In Equipment",
        compute="_compute_where_used_equipment",
    )

    def _compute_where_used_equipment(self):
        Component = self.env['maintenance.equipment.component']
        for lot in self:
            component = Component.search([
                ('lot_id', '=', lot.id),
                ('active_component', '=', True),
            ], limit=1)
            lot.where_used_equipment_id = component.equipment_id.id if component else False

    def action_open_where_used_equipment(self):
        self.ensure_one()
        if not self.where_used_equipment_id:
            return False

        return {
            'type': 'ir.actions.act_window',
            'name': 'Installed In Equipment',
            'res_model': 'maintenance.equipment',
            'view_mode': 'form',
            'res_id': self.where_used_equipment_id.id,
        }

    def _compute_equipment_count(self):
        for lot in self:
            lot.equipment_count = len(lot.equipment_ids)

    def action_open_equipment(self):
        self.ensure_one()

        action = {
            'type': 'ir.actions.act_window',
            'name': 'Equipment',
            'res_model': 'maintenance.equipment',
            'view_mode': 'list,form',
            'domain': [('serial_lot_id', '=', self.id)],
        }

        if self.equipment_count == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.equipment_ids.id,
            })

        return action

    def _get_installed_component_lots_from_production(self):
        self.ensure_one()

        # Find færdigvare-linjen for dette serienummer
        finished_move_line = self.env['stock.move.line'].search([
            ('lot_id', '=', self.id),
            ('state', '=', 'done'),
            ('move_id.production_id', '!=', False),
        ], order='id desc', limit=1)

        if not finished_move_line:
            return self.env['stock.lot']

        production = finished_move_line.move_id.production_id
        if not production:
            return self.env['stock.lot']

        # Hent alle forbrugte råvare-linjer på denne produktion
        raw_move_lines = production.move_raw_ids.move_line_ids.filtered(
            lambda ml: ml.state == 'done' and ml.lot_id and ml.product_id.tracking in ('lot', 'serial')
        )

        # Returnér lots/serials på komponenterne
        component_lots = raw_move_lines.mapped('lot_id').filtered(lambda l: l.id != self.id)
        return component_lots

    def _create_installed_components_from_production(self, equipment):
        self.ensure_one()
        component_lots = self._get_installed_component_lots_from_production()

        Component = self.env['maintenance.equipment.component']
        for lot in component_lots:
            existing = Component.search([
                ('equipment_id', '=', equipment.id),
                ('lot_id', '=', lot.id),
                ('active_component', '=', True),
            ], limit=1)
            if not existing:
                Component.create({
                    'equipment_id': equipment.id,
                    'lot_id': lot.id,
                    'active_component': True,
                })

    def action_create_equipment(self):
        self.ensure_one()

        if self.equipment_ids:
            raise UserError(_("Equipment already exists for this serial number."))

        if not self.track_as_equipment:
            raise UserError(_("This product is not configured to create Equipment."))

        production = self.env['mrp.production'].search([
            ('lot_producing_id', '=', self.id)
        ], limit=1)

        bom = False
        if production and production.bom_id:
            bom = production.bom_id
        elif self.product_id:
            boms = self.env['mrp.bom']._bom_find(products=self.product_id)
            bom = boms.get(self.product_id)

        equipment_vals = {
            'name': self.ref or self.name,
            'serial_lot_id': self.id,
            'product_id': self.product_id.id,
            'partner_id': self.env.company.partner_id.id,
            'partner_ref': self.product_id.default_code or '',
            'serial_no': self.name or '',
            'production_id': production.id if production else False,
            'bom_id': bom.id if bom else False,
        }

        product_template = self.product_id.product_tmpl_id
        if product_template.track_as_equipment and product_template.equipment_category_id:
            equipment_vals['category_id'] = product_template.equipment_category_id.id

        equipment = self.env['maintenance.equipment'].create(equipment_vals)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.equipment',
            'view_mode': 'form',
            'res_id': equipment.id,
        }

    def write(self, vals):
        res = super().write(vals)

        fields_that_matter = {'name', 'ref', 'product_id'}
        if fields_that_matter.intersection(vals.keys()):
            for lot in self:
                equipments = self.env['maintenance.equipment'].search([
                    ('serial_lot_id', '=', lot.id)
                ])
                for equipment in equipments:
                    equipment_vals = {
                        'serial_no': lot.name or '',
                        'name': lot.ref or lot.name,
                    }

                    if lot.product_id:
                        equipment_vals['product_id'] = lot.product_id.id
                        equipment_vals['partner_ref'] = lot.product_id.default_code or ''

                    equipment.write(equipment_vals)
                    equipment._sync_all_from_serial()

        return res