# Copyright 2019 Tecnativa - Pedro M. Baeza
# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _, api, fields, models


class ProductCustomerInfo(models.Model):
    _inherit = "product.supplierinfo"
    _name = "product.customerinfo"
    _description = "Customer Pricelist"

    partner_id = fields.Many2one(string="Customer", help="Customer of this product")
    product_name = fields.Char(string="Customer Product Name")
    product_code = fields.Char(string="Customer Product Code")

    @api.model
    def get_import_templates(self):
        return [
            {
                "label": _("Import Template for Customer Pricelists"),
                "template": "/product_customerinfo/static/xls/"
                "product_customerinfo.xls",
            }
        ]

    @api.model
    def _get_name_search_domain(self, partner_id, operator, name):
        return [
            ("partner_id", "=", partner_id),
            "|",
            ("product_code", operator, name),
            ("product_name", operator, name),
        ]
