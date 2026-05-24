from odoo import models, fields, api, _


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    serial_lot_id = fields.Many2one(
        'stock.lot',
        string="Serial Number Link",
        ondelete='restrict',
    )

    product_id = fields.Many2one(
        'product.product',
        string="Product",
    )

    production_id = fields.Many2one(
        'mrp.production',
        string="Manufacturing Order",
        readonly=True,
    )

    production_name = fields.Char(
        string="MO Name",
        related='production_id.name',
        readonly=True,
    )

    system_id = fields.Many2one(
        'maintenance.equipment.system',
        string='System Number',
    )

    bom_id = fields.Many2one(
        'mrp.bom',
        string='BoM',
        readonly=True,
    )

    bom_code = fields.Char(
        string="BoM Code",
        related='bom_id.code',
        readonly=True,
    )

    model = fields.Char(
        string="Model",
        compute="_compute_model_from_bom",
        store=True,
        readonly=False,
    )

    component_event_ids = fields.One2many(
        'maintenance.equipment.component.event',
        'equipment_id',
        string='Component History',
    )

    last_delivery_partner_id = fields.Many2one(
        'res.partner',
        string="Customer",
        compute="_compute_current_customer",
        store=False,
        readonly=True,
    )

    sales_count = fields.Integer(
        string="Sales",
        compute="_compute_sales_count",
    )

    delivery_count = fields.Integer(
        string="Transfers",
        related='serial_lot_id.delivery_count',
        readonly=True,
    )

    active_request_count = fields.Integer(
        string="Active Maintenance Requests",
        compute="_compute_active_request_count",
    )

    installed_component_ids = fields.One2many(
        'maintenance.equipment.component',
        'equipment_id',
        string='Installed Components',
    )

    active_component_count = fields.Integer(
        string='Installed Components',
        compute='_compute_active_component_count',
    )

    installed_component_serial_search = fields.Char(
        string="Installed Component Serial",
        compute="_compute_installed_component_serial_search",
        search="_search_installed_component_serial_search",
    )

    repair_module_installed = fields.Boolean(
        string="Repair Module Installed",
        compute="_compute_repair_info",
    )

    repair_part_count = fields.Integer(
        string="Repair Parts",
        compute="_compute_repair_info",
    )

    in_repair_count = fields.Integer(
        string="To Do Repairs",
        compute="_compute_repair_info",
    )

    repaired_count = fields.Integer(
        string="Done Repairs",
        compute="_compute_repair_info",
    )

    active_installed_component_ids = fields.One2many(
        'maintenance.equipment.component',
        'equipment_id',
        string='Active Installed Components',
        domain=[('active_component', '=', True)],
    )

    @api.depends('installed_component_ids.lot_id.name', 'installed_component_ids.active_component')
    def _compute_installed_component_serial_search(self):
        for equipment in self:
            active_lots = equipment.installed_component_ids.filtered(
                lambda c: c.active_component and c.lot_id
            ).mapped('lot_id.name')
            equipment.installed_component_serial_search = ', '.join(active_lots)

    def _search_installed_component_serial_search(self, operator, value):
        if not value:
            return []

        allowed = ['=', '!=', 'like', 'ilike', '=like', '=ilike', 'not like', 'not ilike']
        if operator not in allowed:
            operator = 'ilike'

        components = self.env['maintenance.equipment.component'].search([
            ('active_component', '=', True),
            ('lot_id.name', operator, value),
        ])
        equipment_ids = components.mapped('equipment_id').ids
        return [('id', 'in', equipment_ids or [0])]

    @api.depends('serial_lot_id')
    def _compute_current_customer(self):
        Quant = self.env['stock.quant']
        MoveLine = self.env['stock.move.line']
        Component = self.env['maintenance.equipment.component']

        for equipment in self:
            equipment.last_delivery_partner_id = False

            if not equipment.serial_lot_id:
                continue

            # 1) Hvis dette serial selv har lagerstatus
            customer_quant = Quant.search([
                ('lot_id', '=', equipment.serial_lot_id.id),
                ('quantity', '>', 0),
                ('location_id.usage', '=', 'customer'),
            ], limit=1)

            if customer_quant:
                move_line = MoveLine.search([
                    ('lot_id', '=', equipment.serial_lot_id.id),
                    ('state', '=', 'done'),
                    ('location_dest_id.usage', '=', 'customer'),
                    ('picking_id.partner_id', '!=', False),
                ], order='date desc, id desc', limit=1)

                if move_line:
                    equipment.last_delivery_partner_id = move_line.picking_id.partner_id.id
                    continue

            # 2) Hvis serial ligger internt, så skal customer være blank
            internal_quant = Quant.search([
                ('lot_id', '=', equipment.serial_lot_id.id),
                ('quantity', '>', 0),
                ('location_id.usage', '=', 'internal'),
            ], limit=1)

            if internal_quant:
                continue

            # 3) Hvis serial ikke har egen aktiv quant,
            #    så kan det være installeret i et andet Equipment
            component = Component.search([
                ('lot_id', '=', equipment.serial_lot_id.id),
                ('active_component', '=', True),
                ('equipment_id', '!=', equipment.id),
            ], limit=1)

            if component and component.equipment_id:
                equipment.last_delivery_partner_id = component.equipment_id.last_delivery_partner_id.id

    @api.depends('serial_lot_id')
    def _compute_repair_info(self):
        lot_fields = self.env['stock.lot']._fields
        has_repair_fields = all(
            field_name in lot_fields
            for field_name in ['repair_part_count', 'in_repair_count', 'repaired_count']
        )

        for equipment in self:
            equipment.repair_module_installed = bool(equipment.serial_lot_id) and has_repair_fields
            equipment.repair_part_count = 0
            equipment.in_repair_count = 0
            equipment.repaired_count = 0

            if equipment.repair_module_installed:
                equipment.repair_part_count = equipment.serial_lot_id.repair_part_count
                equipment.in_repair_count = equipment.serial_lot_id.in_repair_count
                equipment.repaired_count = equipment.serial_lot_id.repaired_count

    def action_open_repair_parts(self):
        self.ensure_one()
        if not self.repair_module_installed:
            return False

        method = getattr(self.serial_lot_id, 'action_view_ro', None)
        return method() if method else False

    def action_open_lot_repairs(self):
        self.ensure_one()
        if not self.repair_module_installed:
            return False

        method = getattr(self.serial_lot_id, 'action_lot_open_repairs', None)
        return method() if method else False

    def action_open_production(self):
        self.ensure_one()

        if not self.production_id:
            return False

        return {
            'type': 'ir.actions.act_window',
            'name': _('Manufacturing Order'),
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': self.production_id.id,
        }

    @api.depends('installed_component_ids.active_component')
    def _compute_active_component_count(self):
        for equipment in self:
            equipment.active_component_count = len(
                equipment.installed_component_ids.filtered(lambda c: c.active_component)
            )

    @api.depends('serial_lot_id')
    def _compute_sales_count(self):
        StockMoveLine = self.env['stock.move.line']

        for equipment in self:
            equipment.sales_count = 0

            if not equipment.serial_lot_id:
                continue

            move_lines = StockMoveLine.search([
                ('lot_id', '=', equipment.serial_lot_id.id),
                ('state', '=', 'done'),
                ('move_id.sale_line_id', '!=', False),
            ])

            sale_orders = move_lines.mapped('move_id.sale_line_id.order_id')
            equipment.sales_count = len(sale_orders)

    @api.depends('bom_id', 'bom_id.code')
    def _compute_model_from_bom(self):
        for equipment in self:
            equipment.model = equipment.bom_id.code or False

    def _compute_active_request_count(self):
        Repair = self.env['repair.order']

        for equipment in self:
            equipment.active_request_count = 0

            if not equipment.serial_lot_id:
                continue

            equipment.active_request_count = Repair.search_count([
                ('lot_id', '=', equipment.serial_lot_id.id),
                ('state', 'not in', ('done', 'cancel')),
            ])

    def action_open_installed_components(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Installed Components'),
            'res_model': 'maintenance.equipment.component',
            'view_mode': 'list,form',
            'domain': [
                ('equipment_id', '=', self.id),
                ('active_component', '=', True),
            ],
            'context': {
                'default_equipment_id': self.id,
            },
        }

    def _sync_production(self):
        self.ensure_one()

        production = self.env['mrp.production'].search([
            ('lot_producing_id', '=', self.serial_lot_id.id)
        ], limit=1) if self.serial_lot_id else False

        self.with_context(skip_equipment_auto_sync=True).write({
            'production_id': production.id if production else False,
        })


    def _sync_bom(self):
        self.ensure_one()

        if not self.product_id:
            self.with_context(skip_equipment_auto_sync=True).write({
                'bom_id': False,
            })
            return

        bom = False
        if self.production_id and self.production_id.bom_id:
            bom = self.production_id.bom_id
        else:
            boms = self.env['mrp.bom']._bom_find(products=self.product_id)
            bom = boms.get(self.product_id)

        self.with_context(skip_equipment_auto_sync=True).write({
            'bom_id': bom.id if bom else False,
        })

    def _sync_components(self):
        self.ensure_one()
        if not self.serial_lot_id:
            return

        # 1) nulstil installed components
        self.installed_component_ids.write({'active_component': False})

        # 2) nulstil event history
        self._reset_component_history()

        # 3) seed fra produktion
        self.serial_lot_id._create_installed_components_from_production(self)
        self._create_component_history_from_production()

        # 4) replay repairs i rækkefølge
        RepairOrder = self.env['repair.order']
        if 'lot_id' not in RepairOrder._fields:
            return

        repairs = RepairOrder.search(
            [('lot_id', '=', self.serial_lot_id.id)],
            order='id asc'
        )

        for repair in repairs:
            repair._sync_installed_components_to_equipment()

    def _sync_all_from_serial(self):
        for equipment in self:
            equipment._sync_production()
            equipment._sync_bom()
            equipment._sync_components()

            if equipment.serial_lot_id:
                equipment.with_context(skip_equipment_auto_sync=True).write({
                    'serial_no': equipment.serial_lot_id.name or '',
                    'name': equipment.serial_lot_id.ref or equipment.serial_lot_id.name,
                })

    def action_sync_movements(self):
        self.ensure_one()
        self._sync_all_from_serial()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def _apply_repair_line_change(self, product, lots, repair_type):
        self.ensure_one()
        Component = self.env['maintenance.equipment.component']

        if repair_type == 'add':
            for lot in lots:
                existing = Component.search([
                    ('equipment_id', '=', self.id),
                    ('lot_id', '=', lot.id),
                ], limit=1)
                if existing:
                    existing.active_component = True
                else:
                    Component.create({
                        'equipment_id': self.id,
                        'lot_id': lot.id,
                        'active_component': True,
                    })

        elif repair_type in ('remove', 'recycle'):
            if lots:
                existing_components = Component.search([
                    ('equipment_id', '=', self.id),
                    ('lot_id', 'in', lots.ids),
                    ('active_component', '=', True),
                ])
                existing_components.write({'active_component': False})
            elif product:
                existing_components = Component.search([
                    ('equipment_id', '=', self.id),
                    ('product_id', '=', product.id),
                    ('active_component', '=', True),
                ])
                existing_components.write({'active_component': False})

    def _reset_component_history(self):
        self.ensure_one()
        self.component_event_ids.unlink()

    def _create_component_history_from_production(self):
        self.ensure_one()
        if not self.serial_lot_id:
            return

        finished_move_line = self.env['stock.move.line'].search([
            ('lot_id', '=', self.serial_lot_id.id),
            ('state', '=', 'done'),
            ('move_id.production_id', '!=', False),
        ], order='id desc', limit=1)

        if not finished_move_line:
            return

        production = finished_move_line.move_id.production_id
        if not production:
            return

        raw_move_lines = production.move_raw_ids.move_line_ids.filtered(
            lambda ml: ml.state == 'done' and ml.lot_id and ml.product_id.tracking in ('lot', 'serial')
        )

        Event = self.env['maintenance.equipment.component.event']
        for ml in raw_move_lines:
            Event.create({
                'equipment_id': self.id,
                'source_model': 'mrp.production',
                'source_name': production.name,
                'source_ref': f'mrp.production,{production.id}',
                'product_id': ml.product_id.id,
                'removed_lot_id': False,
                'added_lot_id': ml.lot_id.id,
            })

    def action_open_lot_sales(self):
        self.ensure_one()
        if not self.serial_lot_id:
            return False

        move_lines = self.env['stock.move.line'].search([
            ('lot_id', '=', self.serial_lot_id.id),
            ('state', '=', 'done'),
            ('move_id.sale_line_id', '!=', False),
        ])
        sale_orders = move_lines.mapped('move_id.sale_line_id.order_id')

        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales'),
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', sale_orders.ids)],
        }

    def action_open_lot_transfers(self):
        self.ensure_one()
        if not self.serial_lot_id:
            return False

        return self.serial_lot_id.action_lot_open_transfers()

    def action_open_lot_location(self):
        self.ensure_one()
        if not self.serial_lot_id:
            return False

        return self.serial_lot_id.action_lot_open_quants()

    def action_open_lot_traceability(self):
        self.ensure_one()
        if not self.serial_lot_id:
            return False

        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_stock_report")
        action_context = action.get("context", {})

        if isinstance(action_context, str):
            action_context = {}

        action_context.update({
            "active_id": self.serial_lot_id.id,
            "active_ids": [self.serial_lot_id.id],
            "active_model": "stock.lot",
        })

        action["context"] = action_context
        return action

    # AUTOMATIC BEHAVIOR

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('skip_equipment_auto_sync'):
            for record in records.filtered(lambda r: r.serial_lot_id):
                record.with_context(skip_equipment_auto_sync=True)._sync_all_from_serial()
        return records

    def write(self, vals):
        res = super().write(vals)

        if self.env.context.get('skip_equipment_auto_sync'):
            return res

        if any(k in vals for k in ('serial_lot_id', 'product_id', 'production_id')):
            for record in self.filtered(lambda r: r.serial_lot_id):
                record.with_context(skip_equipment_auto_sync=True)._sync_all_from_serial()

        return res
