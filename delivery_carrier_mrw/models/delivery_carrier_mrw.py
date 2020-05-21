from odoo import fields, models, api

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

    @api.multi
    def test_mrw_connection(self):
        pass
