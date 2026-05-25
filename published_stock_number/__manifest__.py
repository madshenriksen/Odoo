# -*- coding: utf-8 -*-
{
    "name": "Published Stock Number",
    "summary": "Highlight products that use published stock numbers",
    "version": "18.0.1.1.0",
    "category": "Inventory/Inventory",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": ["stock", "product", "web"],
    "data": [
        "views/product_template_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "published_stock_number/static/src/js/published_stock_number_confirm.js",
            "published_stock_number/static/src/css/published_stock_number.css",
        ],
    },
    "installable": True,
    "application": False,
}
