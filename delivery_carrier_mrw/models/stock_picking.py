from datetime import date, timedelta

import requests
import werkzeug

from lxml import etree

from odoo import fields, models, api

SELECT_SN = [('S', 'SI'),('N', 'NO')]
TIPOCOBRO = [('1', 'Origen'), ('2', 'Destino')]
RETORNO = [('N', 'Sin retorno'),
           ('D', 'Retorno CD'),
           ('S', 'Retorno mercancía')]
SEGSMS = [('1', 'Preaviso de entrega'),('2', 'Preaviso de recogida')]


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def mrw_send_button(self):
        template = 'delivery_carrier_mrw.TransmEnvio'

        for picking in self:
            if picking.carrier_id and picking.carrier_id.mrw_debug:
                url = picking.carrier_id.mrw_test_url or ''
            else:
                url = picking.carrier_id.mrw_test_url or ''

            data = {
                'franchise': picking.carrier_id.mrw_franchise_code or '',
                'subscriber': picking.carrier_id.mrw_subscriber_code or '',
                'department':picking.carrier_id.mrw_department_code or '',
                'username':picking.carrier_id.mrw_username or '',
                'password':picking.carrier_id.mrw_password or '',
                'address_code': '01',
                'address_street_code': 'CL',
                'address_street': picking.partner_id.street or '',
                'address_number': '',
                'address_street2': picking.partner_id.street or '',
                'address_zip': picking.partner_id.zip or '',
                'address_city': picking.partner_id.city or '',
                'address_state': picking.partner_id.state_id and
                                 picking.partner_id.state_id.name or '',
                'partner_vat': picking.partner_id.vat or '',
                'partner_name': picking.partner_id.name or '',
                'partner_phone': picking.partner_id.phone or
                                 picking.partner_id.mobile or '',
                'partner_contact': '',
                'partner_att': '',
                'note': picking.note,
                'date': date.today().strftime('%d/%m/%Y'),
                'reference': '',
                'in_franchise': 'E',
                'service_code': picking.carrier_id.mrw_service_code or '',
                'number_of_packages': picking.number_of_packages,
                'weight': picking.shipping_weight,
                'saturday': 'N',
                'cash_on_delivery': 'N',
                'cash_on_delivery_amount': '0.00',
            }

            response = ''

            headers = {
                'Content-Type': 'text/xml',
                'SOAPAction': 'http://www.mrw.es/TransmEnvio'
            }

            # Cargar plantilla envio
            xml_transaction = self.env.ref(template).render(data).decode()

            try:
                r = requests.post(url, data=xml_transaction, headers=headers,
                                  timeout=60)
                r.raise_for_status()
                response = werkzeug.utils.unescape(r.content.decode())
                for node in etree.fromstring(response):
                    pass

            except Exception as e:
                response = "timeout"


            return True


    @api.multi
    def mrw_sticker_button(self):
        template = 'delivery_carrier_mrw.TransmEtiquetaEnvio'

        for picking in self:
            if picking.carrier_id and picking.carrier_id.mrw_debug:
                url = picking.carrier_id.mrw_test_url or ''
            else:
                url = picking.carrier_id.mrw_test_url or ''

            data = {
                'franchise': picking.carrier_id.mrw_franchise_code or '',
                'subscriber': picking.carrier_id.mrw_subscriber_code or '',
                'department': picking.carrier_id.mrw_department_code or '',
                'username': picking.carrier_id.mrw_username or '',
                'password': picking.carrier_id.mrw_password or '',
                'delivery_number': '',
                'delivery_number_split': '',
                'date_start': '',
                'date_end': '',
                'sticker_type': '0',
                'top_margin': '1100',
                'left_margin': '659',
            }

            response = ''

            headers = {
                'Content-Type': 'text/xml',
                'SOAPAction': 'http://www.mrw.es/EtiquetaEnvio,'
            }

            # Cargar plantilla envio
            xml_transaction = self.env.ref(template).render(data).decode()

            try:
                r = requests.post(url, data=xml_transaction, headers=headers,
                                  timeout=60)
                r.raise_for_status()
                response = werkzeug.utils.unescape(r.content.decode())
            except Exception:
                response = "timeout"

            return response
