from lxml import etree
from datetime import date
import base64
import logging

from odoo import _, api, exceptions, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from zeep import Client, Plugin
    from zeep.transports import Transport
    from zeep.plugins import HistoryPlugin

except (ImportError, IOError) as err:
    _logger.debug(err)

SERVICETYPES = [
    ('0000', 'Urgente 10'),
    ('0100', 'Urgente 12'),
    ('0110', 'Urgente 14'),
    ('0200', 'Urgente 19'),
    ('0205', 'Urgente 19 Expedición'),
    ('0210', 'Urgente 19 + 40 Kg'),
    ('0215', 'Urgente 19 Portugal'),
    ('0220', 'Urgente 22'),
    ('0225', '48 Urgente Portugal'),
    ('0230', 'Bag 19'),
    ('0235', 'Bag 14'),
    ('0300', 'Económico'),
    ('0310', 'Económico +40 Kg'),
    ('0350', 'Económico Interinsular'),
    ('0360', 'Marítimo Baleares'),
    ('0400', 'Express Documentos'),
    ('0450', 'Express 2 Kg'),
    ('0480', 'Caja Express 3 Kg'),
    ('0490', 'Documentos 14')]


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('mrw', "MRW")])

    mrw_franchise_code = fields.Char(
        string='Franchise Code',
        help="Franchise code for MRW carrier company."
    )
    mrw_subscriber_code = fields.Char(
        string='Subscriber Code',
        help="Subscriber code for MRW carrier company."
    )
    mrw_department_code = fields.Char(
        string='Department Code',
        help="Department code for MRW carrier company."
    )
    mrw_username = fields.Char(
        string='Username',
    )
    mrw_password = fields.Char(
        string='Password',
    )
    mrw_service_code = fields.Selection(
        selection=SERVICETYPES,
        string='Service code',
    )
    mrw_intl_service_code = fields.Selection(
        selection=SERVICETYPES,
        string='International service code',
    )
    mrw_debug = fields.Boolean(
        string='Test environment',
        default=True,
        help='If selected, the test environment will be enabled'
    )
    mrw_prod_url = fields.Char(
        string='Production URL'
    )
    mrw_test_url = fields.Char(
        string='Testing URL'
    )
    mrw_price_method = fields.Selection(
        selection=[
            ('fixed', 'Fixed price'),
            ('base_on_rule', 'Based on Rules'),
        ],
        string='Price method',
        default='fixed',
    )

    @api.model
    def mrw_wsdl_get(self, service):
        if service == 'TransmEnvio':
            return 'http://sagec-test.mrw.es/MRWEnvio.asmx?WSDL'
        if service == 'TransmEtiquetaEnvio':
            return 'http://sagec-test.mrw.es/MRWEnvio.asmx?WSDL'
        raise NotImplementedError

    @api.model
    def mrw_soap_send(self, service, method, data):
        def trace(title, data):
            _logger.debug('%s %s: %s' % (
                method, title, etree.tostring(data['envelope'])))


        if method == 'TransmEnvio':
            template = 'delivery_carrier_mrw.TransmEnvio'
        elif method == 'TransmEtiquetaEnvio':
            template = 'delivery_carrier_mrw.TransmEtiquetaEnvio'
        else:
            template = False

        if template:
            xml_root = self.env.ref(template).render(data).decode()

        else:
            raise UserError(
                _("Error.\n"
                  "No MRW template service found.")
            )

        history = HistoryPlugin()
        client = Client(
            wsdl='http://sagec-test.mrw.es/MRWEnvio.asmx?WSDL',
            service_name=service,
            transport=Transport(),
            plugins=[history, xml_root],
        )
        cli = client.bind()
        response = cli[method](**data)
        trace('Request', history.last_sent)
        trace('Response', history.last_received)
        return response

    def mrw_get_tracking_link(self, picking):
        self.ensure_one()
        if self.mrw_debug:
            url_base = self.mrw_test_url
        else:
            url_base = self.mrw_prod_url

        data = '?Franq=%s&Ab=%s&Dep=&Pwd=%s&Usr=%s&NumEnv=%s' % (
            self.mrw_franchise_code, self.mrw_subscriber_code,
            self.mrw_password, self.mrw_username, picking.customer_tracking_ref
        )

        return url_base + data

    def mrw_rate_shipment(self, order):
        return getattr(
            self, '%s_rate_shipment' % self.mrw_price_method)(order)

    def mrw_send_shipping(self, pickings):
        return [self.mrw_create_shipping(p) for p in pickings]

    def mrw_cancel_shipment(self, pickings):
        # Note: MRW API not provide shipment cancel service
        raise UserError(_("You can't cancel MRW shipping."))

    def mrw_create_shipping(self, picking):
        self.ensure_one()
        partner = picking.partner_id
        company = picking.company_id
        phone = (partner.phone and partner.phone.replace(' ', '') or '')
        mobile = (partner.mobile and partner.mobile.replace(' ', '') or '')
        company_mobile = (company.partner_id.mobile and
                          company.partner_id.mobile.replace(' ', '') or '')
        data = {
            'franchise': picking.carrier_id.mrw_franchise_code or '',
            'subscriber': picking.carrier_id.mrw_subscriber_code or '',
            'department': '', # Not used
            'username': picking.carrier_id.mrw_username or '',
            'password': picking.carrier_id.mrw_password or '',
            'address_code': '01',
            'address_street_code': 'CL',
            'address_street': partner.street or '',
            'address_number': '',
            'address_street2': partner.street or '',
            'address_zip': partner.zip or '46815',
            'address_city': partner.city or '',
            'address_state': partner.state_id and
                             partner.state_id.name or '',
            'partner_vat': partner.vat or '',
            'partner_name': 'aaa',
            'partner_phone': phone or mobile,
            'partner_contact': '',
            'partner_att': '',
            'company_phone': company_mobile,
            'note': picking.note,
            'date': date.today().strftime('%d/%m/%Y'),
            'delivery_jumps': '1',
            'reference': picking.name,
            'in_franchise': 'E',
            'service_code': picking.carrier_id.mrw_service_code or '',
            'number_of_packages': int(picking.number_of_packages),
            'weight': picking.shipping_weight,
            'saturday': 'N',
            'cash_on_delivery': 'N',
            'cash_on_delivery_amount': '0.00',
            'cash_on_delivery_percentage': '0',
            'delivery_product_type': '',
            'products_cost': '',
            'delivery_time_from': '',
            'delivery_confirmation': '',
            'delivery_with_return': '',
            'delivery_management': '',
            'urgent_delivery': '',
            'promotion_delivery': '',
            'envelope_number': '',
            'delivery_frequency': '',
            'delivery_time_interval': '',
            'delivery_due': '',
            'delivery_mask_types': '',
            'delivery_mask_fields': '',
            'delivery_assistant': '',









        }

        res = self.mrw_soap_send('TransmEnvio', 'TransmEnvio', data)

        if res['mensaje'] == 'ERROR':
            raise exceptions.UserError(
                _('SEUR exception: %s') % res['mensaje'])
        picking.carrier_tracking_ref = res['ECB']['string'][0]
        if self.seur_label_format == 'txt':
            label_content = base64.b64encode(
                res['traza'].replace('CI10', 'CI28'))
        else:
            label_content = res['PDF']
        self.env['ir.attachment'].create({
            'name': 'SEUR %s' % picking.carrier_tracking_ref,
            'datas': label_content,
            'datas_fname': 'seur_%s.%s' % (
                picking.carrier_tracking_ref, self.seur_label_format),
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'mimetype': 'application/%s' % self.seur_label_format,
        })
        res = getattr(
            self, '%s_send_shipping' % self.seur_price_method)(picking)[0]
        res['tracking_number'] = picking.carrier_tracking_ref
        return res
