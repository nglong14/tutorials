from odoo import fields, models


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

    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'Property type name must be unique',
    )
