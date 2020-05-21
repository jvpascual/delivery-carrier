#   2020 Trey - Roberto Lizana <roberto@trey.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tests.common import TransactionCase


class TestDeliveryCarrierSeur(TransactionCase):

    def setUp(self):
        super().setUp()
        product_shipping_cost = self.env['product.product'].create({
            'type': 'service',
            'name': 'Shipping costs',
            'standard_price': 10,
            'list_price': 100,
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'MRW',
            'type': 'mrw',
            'product_id': product_shipping_cost.id,
        })

    def test_soap_connection(self):
        response = self.carrier.mrw_test_connection()
        self.assertTrue(response)

    def test_picking(self):
        product = self.env.ref('product.product_delivery_01')
        partner = self.env.ref('base.res_partner_12')
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'carrier_id': self.carrier.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 10})]
        })
        sale.get_delivery_price()
        sale.set_delivery_line()
        self.assertEquals(len(sale.order_line), 2)
        sale.action_confirm()
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.carrier_id, self.carrier)
        picking.action_confirm()
        picking.action_assign()
        # picking.action_done()
