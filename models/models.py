# -*- coding: utf-8 -*-

from odoo import models, fields, api

class InvoiceMulticurrency(models.Model):
    _inherit = 'account.move.line'
     
    price_unit_currency= fields.Float(string='Unit Price', digits='Product Price')
    price_subtotal_currency = fields.Monetary(string='Subtotal', store=True, readonly=True, currency_field='always_set_currency_id')
    price_total_currency = fields.Monetary(string='Total', store=True, readonly=True, currency_field='always_set_currency_id')

    def _get_computed_price_unit_currency(self):
        self.ensure_one()

        if not self.product_id:
            return self.price_unit_currency
        elif self.move_id.is_sale_document(include_receipts=True):
            # Out invoice.
            price_unit = self.product_id.lst_price
        elif self.move_id.is_purchase_document(include_receipts=True):
            # In invoice.
            price_unit = self.product_id.standard_price
        else:
            return self.price_unit

        