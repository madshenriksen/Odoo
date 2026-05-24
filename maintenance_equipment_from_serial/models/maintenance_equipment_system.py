from odoo import models, fields


class MaintenanceEquipmentSystem(models.Model):
    _name = 'maintenance.equipment.system'
    _description = 'Equipment System'
    _order = 'name'

    name = fields.Char(
        string='System Number',
        required=True,
    )

    responsible_id = fields.Many2one(
        'res.users',
        string='Responsible',
    )

    note = fields.Text(
        string='Comments',
    )

    equipment_ids = fields.One2many(
        'maintenance.equipment',
        'system_id',
        string='Equipment',
    )

    equipment_count = fields.Integer(
        string='Equipment Count',
        compute='_compute_counts',
    )

    maintenance_count = fields.Integer(
        string='Maintenance Count',
        compute='_compute_counts',
    )

    def _compute_counts(self):
        MaintenanceRequest = self.env['maintenance.request']

        for system in self:
            system.equipment_count = len(system.equipment_ids)
            system.maintenance_count = MaintenanceRequest.search_count([
                ('equipment_id.system_id', '=', system.id),
            ])

    def action_open_equipment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Equipment',
            'res_model': 'maintenance.equipment',
            'view_mode': 'list,form',
            'domain': [('system_id', '=', self.id)],
            'context': {
                'default_system_id': self.id,
            },
        }

    def action_open_maintenance_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maintenance Requests',
            'res_model': 'maintenance.request',
            'view_mode': 'list,form',
            'domain': [('equipment_id.system_id', '=', self.id)],
        }