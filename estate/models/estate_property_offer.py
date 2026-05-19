from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Estate Property Offer'

    def _reference_date(self):
        self.ensure_one()
        if self.create_date:
            return fields.Datetime.context_timestamp(self, self.create_date).date()
        return fields.Date.context_today(self)

    price = fields.Float()
    validity = fields.Integer(default=7)
    date_deadline = fields.Date(
        compute='_compute_date_deadline',
        inverse='_inverse_date_deadline',
    )
    status = fields.Selection(
        selection=[
            ('accepted', 'Accepted'),
            ('refused', 'Refused'),
        ],
        copy=False,
    )
    partner_id = fields.Many2one('res.partner', required=True)
    property_id = fields.Many2one(
        'estate.property',
        required=True,
        ondelete='cascade',
    )

    @api.depends('create_date', 'validity')
    def _compute_date_deadline(self):
        for offer in self:
            base = offer._reference_date()
            offer.date_deadline = base + timedelta(days=offer.validity)

    def _inverse_date_deadline(self):
        for offer in self:
            base = offer._reference_date()
            if offer.date_deadline:
                offer.validity = (offer.date_deadline - base).days

    def action_accept(self):
        for offer in self:
            if offer.property_id.state in ('sold', 'cancelled'):
                raise UserError(_("Cannot accept an offer on a sold or cancelled property."))
            if offer.property_id.offer_ids.filtered(
                lambda o: o.status == 'accepted' and o.id != offer.id
            ):
                raise UserError(_("Only one offer can be accepted per property."))
            offer.status = 'accepted'
            (offer.property_id.offer_ids - offer).write({'status': 'refused'})
            offer.property_id.write({
                'buyer_id': offer.partner_id.id,
                'state': 'offer_accepted',
            })

    def action_refuse(self):
        self.write({'status': 'refused'})

    _offer_price_positive = models.Constraint(
        'CHECK (price > 0)',
        'The offer price must be strictly positive',
    )
