


import requests
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, ValidationError


class ProviderOmanPost(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[
        ('vw_oman_post', 'Oman Post'),
        ], ondelete={'vw_oman_post': lambda recs: recs.write({
            'delivery_type': 'fixed',
            'fixed_price': 0,
        })})
    
    vw_oman_post_service = fields.Selection(
        string="Service",
        selection=[
            ("EMS", "Express Mail Service"), 
            ("Parcel", "Parcel"), 
            ("ASYAD Express International", "ASYAD Express International"), 
            ("Ordinary Letter", "Ordinary Letter"), 
            ("Registered Mail", "Registered Mail"),
        ],
        help="There are differ in time and price.",
    )
    
    ###############################################################
    # Delivery Provider
    ###############################################################
    def vw_oman_post_rate_shipment(self, order):
        carrier = self._match_address(order.partner_shipping_id)
        if not carrier:
            return {'success': False,
                    'price': 0.0,
                    'error_message': _('Error: this delivery method is not available for this address.'),
                    'warning_message': False}

        type = self.vw_oman_post_service
        print(type)
        print('------------------------------')
        try:
            price_unit = self._get_price_available(order, type)
        except UserError as e:
            return {'success': False,
                    'price': 0.0,
                    'error_message': e.args[0],
                    'warning_message': False}
        if order.company_id.currency_id.id != order.pricelist_id.currency_id.id:
            price_unit = order.company_id.currency_id._convert(
                price_unit, order.pricelist_id.currency_id, order.company_id, order.date_order or fields.Date.today())

        return {'success': True,
                'price': price_unit,
                'error_message': False,
                'warning_message': False}

    def vw_oman_post_send_shipping(self, pickings):
        res = []
        type = self.vw_oman_post_service
        for p in pickings:
            carrier = self._match_address(p.partner_id)
            if not carrier:
                raise ValidationError(_('There is no matching delivery rule.'))
            res = res + [{
                'exact_price': p.carrier_id._get_price_available(p.sale_id, type) if p.sale_id else 0.0,
                'tracking_number': False
                }]
        return res

    def vw_oman_post_get_tracking_link(self, picking):
        return False

    def vw_oman_post_cancel_shipment(self, pickings):
        raise NotImplementedError()
    
    
    ###############################################################
    # Utilities
    ###############################################################
    def _get_price_available(self, order, type):
        '''
        Calculate delivery price for order based on the type. 
        
        :param type: The type of delivery. This is service name from Oman post office
        :param order: the target order
        '''
        self.ensure_one()
        self = self.sudo()
        order = order.sudo()
        total = weight = volume = quantity = 0
        total_delivery = 0.0
        for line in order.order_line:
            if line.state == 'cancel':
                continue
            if line.is_delivery:
                total_delivery += line.price_total
            if not line.product_id or line.is_delivery:
                continue
            qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
            weight += (line.product_id.weight or 0.0) * qty
            volume += (line.product_id.volume or 0.0) * qty
            quantity += qty
        total = (order.amount_total or 0.0) - total_delivery
    
        total = order.currency_id._convert(
            total, order.company_id.currency_id, order.company_id, order.date_order or fields.Date.today())
        
        # maso 2021: fetch customer country
        country = order.partner_shipping_id.country_id.code
        price = self._get_price_from_picking(total, weight, volume, quantity, country, type)
        # XXX: maso, 2021: convert Oman Rial to order currency
        OMR = self.env['res.currency'].search([('name', '=', 'OMR')])
        price = order.company_id.currency_id._convert(
                    price,
                    OMR,
                    order.company_id, 
                    order.date_order or fields.Date.today())
        # price = order.company_id.currency_id.compute(price, OMR)
        return price

    def _get_price_from_picking(self, total, weight, volume, quantity, country, type):
        '''
        :param country: country code of the destination
        :param type: this is mail type or service name of the post here is supported
         - EMS
         - Parcel
         - ASYAD Express International
         - Registered Mail
         - Ordinary Letter
        '''
        price = 0.0
        criteria_found = False
        # TODO: maso, 2021: I do not know if this part is required in oman post
        price_dict = self._get_price_dict(total, weight, volume, quantity)
        if self.free_over and total >= self.amount:
            return 0
        # XXX: fetch price from server for weight and country
        url='https://omanpost.om/en/complete-rate-calculator/'
        # method: post
        #-------- form data
        # functionname: calculate
        # arguments[]: 0.68
        # arguments[]: AE
        res = requests.post(url=url, data={
                'functionname': 'calculate',
                'arguments[]': [weight, country]
            }, timeout=60)
        service = False
        js = res.json()
        # TODO: maso, 2021: check if response is success
        if isinstance(js['data'], dict) and js['data'].has_key('Status'):
            raise ValidationError(js['data']['Message'])
        for item in js['data']:
            if item['ServiceName'] == type:
                service = item
                break
        if not service:
            raise ValidationError(_('The delivery type is not supported.'))
        return float(service['TotalAmount'])
    
    def _get_price_dict(self, total, weight, volume, quantity):
        '''
        Hook allowing to retrieve dict to be used in _get_price_from_picking() function.
        Hook to be overridden when we need to add some field to product and use it in 
        variable factor from price rules. 
        '''
        return {
            'price': total,
            'volume': volume,
            'weight': weight,
            'wv': volume * weight,
            'quantity': quantity
        }
    
    



