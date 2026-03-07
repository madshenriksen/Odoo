from odoo import models


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    def _get_component_lines(self):
        self.ensure_one()

        for field_name in ('move_ids', 'repair_line_ids', 'parts_ids', 'operation_ids'):
            if field_name in self._fields:
                return self[field_name]

        return self.env['repair.line']

    def _sync_installed_components_to_equipment(self):
        Equipment = self.env['maintenance.equipment']
        Event = self.env['maintenance.equipment.component.event']

        for repair in self:
            if 'lot_id' not in repair._fields or not repair.lot_id:
                continue

            equipment = Equipment.search([
                ('serial_lot_id', '=', repair.lot_id.id),
            ], limit=1)

            if not equipment:
                continue

            lines = repair._get_component_lines()

            add_lines = lines.filtered(
                lambda l: 'repair_line_type' in l._fields
                and l.repair_line_type == 'add'
                and (not 'picked' in l._fields or l.picked)
            )
            remove_lines = lines.filtered(
                lambda l: 'repair_line_type' in l._fields
                and l.repair_line_type in ('remove', 'recycle')
                and (not 'picked' in l._fields or l.picked)
            )

            # først anvend remove
            for line in remove_lines:
                lots = line.lot_ids if 'lot_ids' in line._fields else self.env['stock.lot']
                equipment._apply_repair_line_change(
                    product=line.product_id if 'product_id' in line._fields else False,
                    lots=lots,
                    repair_type=line.repair_line_type,
                )

            # derefter add
            for line in add_lines:
                lots = line.lot_ids if 'lot_ids' in line._fields else self.env['stock.lot']
                equipment._apply_repair_line_change(
                    product=line.product_id if 'product_id' in line._fields else False,
                    lots=lots,
                    repair_type='add',
                )

            # event history: par remove/add pr. produkt så godt som muligt
            products = (remove_lines.mapped('product_id') | add_lines.mapped('product_id'))
            for product in products:
                product_remove_lines = remove_lines.filtered(lambda l: l.product_id == product)
                product_add_lines = add_lines.filtered(lambda l: l.product_id == product)

                removed_lots = product_remove_lines.mapped('lot_ids')
                added_lots = product_add_lines.mapped('lot_ids')

                max_len = max(len(removed_lots), len(added_lots), 1)

                for idx in range(max_len):
                    removed_lot = removed_lots[idx] if idx < len(removed_lots) else False
                    added_lot = added_lots[idx] if idx < len(added_lots) else False

                    Event.create({
                        'equipment_id': equipment.id,
                        'source_model': 'repair.order',
                        'source_name': repair.name,
                        'source_ref': f'repair.order,{repair.id}',
                        'product_id': product.id if product else False,
                        'removed_lot_id': removed_lot.id if removed_lot else False,
                        'added_lot_id': added_lot.id if added_lot else False,
                    })

    def write(self, vals):
        res = super().write(vals)

        if 'state' in vals:
            finished_repairs = self.filtered(lambda r: r.state in ('done', 'repaired'))
            if finished_repairs:
                finished_repairs._sync_installed_components_to_equipment()

        return res