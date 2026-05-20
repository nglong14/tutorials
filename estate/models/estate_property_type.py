from odoo import api, fields, models


class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Real Estate Property Type'
    _order = 'sequence, name'

    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(required=True)
    property_ids = fields.One2many(
        'estate.property',
        'property_type_id',
        string='Properties',
    )
    offer_ids = fields.One2many(
        'estate.property.offer',
        'property_type_id',
        string='Offers',
    )
    offer_count = fields.Integer(compute='_compute_offer_count')

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for prop_type in self:
            prop_type.offer_count = len(prop_type.offer_ids)

    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'Property type name must be unique',
    )
