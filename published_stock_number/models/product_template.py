# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    published_stock_number = fields.Boolean(
        string="Published Stock Number",
        help=(
            "Mark this product as a Published Stock Number. "
            "Use extra care before changing product data when this option is enabled."
        ),
        default=False,
    )
