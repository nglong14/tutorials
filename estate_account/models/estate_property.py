from odoo import Command, models


class EstateProperty(models.Model):
    _inherit = 'estate.property'

    def action_sold(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        for prop in self:
            self.env['account.move'].create({
                'partner_id': prop.buyer_id.id,
                'move_type': 'out_invoice',
                'journal_id': journal.id,
                'invoice_line_ids': [
                    Command.create({
                        'name': prop.name,
                        'quantity': 1,
                        'price_unit': prop.selling_price * 6 / 100,
                    }),
                    Command.create({
                        'name': 'Administrative fees',
                        'quantity': 1,
                        'price_unit': 100,
                    }),
                ],
            })
        return super().action_sold()
