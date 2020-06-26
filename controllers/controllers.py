# -*- coding: utf-8 -*-
# from odoo import http


# class InvoiceMulticurrency(http.Controller):
#     @http.route('/invoice_multicurrency/invoice_multicurrency/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/invoice_multicurrency/invoice_multicurrency/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('invoice_multicurrency.listing', {
#             'root': '/invoice_multicurrency/invoice_multicurrency',
#             'objects': http.request.env['invoice_multicurrency.invoice_multicurrency'].search([]),
#         })

#     @http.route('/invoice_multicurrency/invoice_multicurrency/objects/<model("invoice_multicurrency.invoice_multicurrency"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('invoice_multicurrency.object', {
#             'object': obj
#         })
