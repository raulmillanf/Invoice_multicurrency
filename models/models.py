# -*- coding: utf-8 -*-

from odoo import models, fields, api

class InvoiceMulticurrency(models.Model):
    _inherit = 'account.move.line'
     
    price_unit_currency= fields.Float(string='Precio unitario', digits='Product Price', readonly=True)
    price_subtotal_currency = fields.Monetary(string='Subtotal', store=True, readonly=True, currency_field='always_set_currency_id_base')
    price_total_currency = fields.Monetary(string='Total', store=True, readonly=True, currency_field='always_set_currency_id_base')
    always_set_currency_id_base = fields.Many2one('res.currency', string='Moneda base', compute='_compute_always_set_currency_id_base')
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    #amount_untaxed_currency = fields.Monetary(string='Base imponible', store=True, readonly=True, tracking=True, compute='_compute_amount')
    #amount_total_currency = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_amount',inverse='_inverse_amount_total')

    def _get_computed_price_unit_currency(self):
        self.ensure_one()

        if not self.product_id:
            return self.price_unit_currency
        elif self.move_id.is_sale_document(include_receipts=True):
           
            price_unit_currency = self.product_id.lst_price
        elif self.move_id.is_purchase_document(include_receipts=True):
            
            price_unit_currency = self.product_id.standard_price
        else:
            return self.price_unit_currency
        if self.product_uom_id != self.product_id.uom_id:
            price_unit_currency = self.product_id.uom_id._compute_price(price_unit_currency, self.product_uom_id)

        return price_unit_currency
    @api.depends('price_unit','amount_currency')
    def _get_onchange_price_unit_currency(self):
        self.ensure_one()
        price_unit_currency = self.price_unit_currency
        price_unit = self.price_unit 
        currency_rate = self.company_id.currency_id.rate
        price_unit_currency = price_unit * currency_rate
        return price_unit_currency
        
    #def _get_price_total_and_subtotal_currency(self, price_unit_currency=None, quantity=None, discount=None, currency=None, product=None, partner=None, taxes=None, move_type=None):
    #    self.ensure_one()
    #    return self._get_price_total_and_subtotal_model_currency(
    #        price_unit_currency=price_unit_currency or self.price_unit_currency,
    #        quantity=quantity or self.quantity,
    #        discount=discount or self.discount,
    #        currency=currency or self.currency_id,
    #        product=product or self.product_id,
    #        partner=partner or self.partner_id,
    #        taxes=taxes or self.tax_ids,
    #        move_type=move_type or self.move_id.type,
    #    )
    @api.model
    def _get_price_total_and_subtotal_currency(self, price_unit_currency=None, quantity=None, discount=None, currency=None, product=None, partner=None, taxes=None, move_type=None):
        self.ensure_one()
        
        res = {}
        price_unit_currency=price_unit_currency or self.price_unit_currency
        quantity=quantity or self.quantity
        discount = discount or self.discount or 0.0
        currency=currency or self.currency_id
        product=product or self.product_id
        partner=partner or self.partner_id
        taxes=taxes or self.tax_ids
        move_type=move_type or self.move_id.type
        price_unit_currency_wo_discount = price_unit_currency * (1 - (discount / 100.0))
        subtotal_currency = quantity * price_unit_currency_wo_discount

        if taxes:
            taxes_res = taxes._origin.compute_all(price_unit_currency_wo_discount,
                quantity=quantity, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal_currency'] = taxes_res['total_excluded']
            res['price_total_currency '] = taxes_res['total_included']
        else:
            res['price_total_currency'] = res['price_subtotal_currency'] = subtotal_currency    
        
    @api.onchange('product_id')
    def _onchange_product_id_currency(self):
        for line in self:
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                continue
         
            line.price_unit_currency = line._get_computed_price_unit_currency()
            if line.tax_ids and line.move_id.fiscal_position_id:
                line.price_unit_currency = line._get_price_total_and_subtotal_currency()['price_subtotal_currency']
                
            
    #def _get_fields_onchange_subtotal_cu(self, price_subtotal_currency=None, move_type=None, currency=None, company=None, date=None):
    #    self.ensure_one()
    #    return self._get_fields_onchange_subtotal_model_cu(
    #        price_subtotal_currency = price_subtotal_currency or self.price_subtotal_currency,
    #        move_type=move_type or self.move_id.type,
    #        currency=currency or self.currency_id,
    #        company=company or self.move_id.company_id,
    #        date=date or self.move_id.date,
    #    )

    @api.model
    def get_inbound_types(self, include_receipts=True):
        return ['out_invoice', 'in_refund'] + (include_receipts and ['out_receipt'] or [])
    @api.model
    def _get_fields_onchange_subtotal_cu(self, price_subtotal_currency=None, move_type=None, currency=None, company=None, date=None):
            
        price_subtotal_currency = price_subtotal_currency or self.price_subtotal_currency
        move_type=move_type or self.move_id.type
        currency=currency or self.currency_id
        company=company or self.move_id.company_id
        date=date or self.move_id.date
        
        if move_type in self.move_id.get_outbound_types():
            sign = 1
        elif move_type in self.move_id.get_inbound_types():
            sign = -1
        else:
            sign = 1
        price_subtotal_currency *= sign
       
        return {
                'amount_currency': 0.0,
                'debit': price_subtotal_currency > 0.0 and price_subtotal_currency or 0.0,
                'credit': price_subtotal_currency < 0.0 and -price_subtotal_currency or 0.0,
            }
    @api.onchange('quantity', 'discount', 'price_unit', 'tax_ids')
    def _onchange_price_subtotal_currency(self):
        for line in self:
            if not line.move_id.is_invoice(include_receipts=True):
                continue
 
                
            line._get_price_total_and_subtotal_currency()
            line._get_fields_onchange_subtotal_cu()
            line._get_onchange_price_unit_currency()    
    
    @api.depends('currency_id')
    def _compute_always_set_currency_id_base(self):
        for line in self:
            line.always_set_currency_id_base = line.company_currency_id

    def _get_fields_onchange_balance_cu(self, quantity=None, discount=None, balance=None, move_type=None, currency=None, taxes=None, price_subtotal_currency=None):
        self.ensure_one()
        return self._get_fields_onchange_balance_model(
            quantity=quantity or self.quantity,
            discount=discount or self.discount,
            balance=balance or self.balance,
            move_type=move_type or self.move_id.type,
            currency=currency or self.currency_id or self.move_id.currency_id,
            taxes=taxes or self.tax_ids,
            price_subtotal_currency=price_subtotal_currency or self.price_subtotal_currency,
        )
        
    #Apesar de que la moneda sea extranjera, se toma la moneda base para efectos contables.
    #@api.depends('amount_untaxed_currency','amount_total_currency')
    #def _get_accounting_on_base_currency(self, amount_untaxed_currency, amount_total_currency,amount_untaxed_signed,amount_total_signed):
    #    amount_untaxed_currency = self.amount_untaxed_currency
    #    amount_total_currency = self.amount_total_currency
    #    amount_total_signed = self.amount_total_signed
    #    amount_untaxed_currency = self.amount_untaxed_signed
    #    company_currency = self.company_id.currency_id
        
    #    if self.currency_id and self.currency_id != company_currency:
    #        amount_total_signed = amount_total_currency
    #        amount_untaxed_signed = amount_untaxed_currency
    #price_subtotal_currency._get_accounting_on_base_currency()
    
       
      

        