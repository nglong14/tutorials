from dateutil.relativedelta import relativedelta

from odoo import api, models, fields


class EstatePropertyTag(models.Model):
    _name = 'estate.property.tag'
    _description = 'Real Estate Property Tag'

    name = fields.Char(required=True)


class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Estate Property'

    name = fields.Char()
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date(
        copy=False,
        default=lambda self: fields.Date.today() + relativedelta(months=3),
    )
    expected_price = fields.Float()
    selling_price = fields.Float(
        compute='_compute_selling_price',
        readonly=True,
        copy=False,
    )
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    total_area = fields.Integer(
        compute='_compute_total_area',
        string='Total Area (sqm)',
    )
    best_price = fields.Float(compute='_compute_best_price')
    garden_orientation = fields.Selection(selection=[('north', 'North'), ('south', 'South'), ('east', 'East'), ('west', 'West')])
    state = fields.Selection(
        selection=[
            ('new', 'New'),
            ('offer_received', 'Offer Received'),
            ('offer_accepted', 'Offer Accepted'),
            ('sold', 'Sold'),
            ('cancelled', 'Cancelled'),
        ],
        required=True,
        copy=False,
        default='new',
    )

    buyer_id = fields.Many2one('res.partner', string='Buyer', copy=False)
    salesperson_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        default=lambda self: self.env.user,
    )
    tag_ids = fields.Many2many('estate.property.tag', string='Tags')
    offer_ids = fields.One2many('estate.property.offer', 'property_id', string='Offers')

    active = fields.Boolean(default=False)

    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for prop in self:
            prop.total_area = (prop.living_area or 0) + (prop.garden_area or 0)

    @api.depends('offer_ids.price')
    def _compute_best_price(self):
        for prop in self:
            prices = prop.offer_ids.mapped('price')
            prop.best_price = max(prices) if prices else 0.0

    @api.depends('offer_ids.price', 'offer_ids.status')
    def _compute_selling_price(self):
        for prop in self:
            accepted = prop.offer_ids.filtered(lambda o: o.status == 'accepted')
            prop.selling_price = accepted[:1].price if accepted else 0.0

    @api.onchange('garden')
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = False
            self.garden_orientation = False

    _name_required = models.Constraint(
        'CHECK (name IS NOT NULL)',
        'Name is required',
    )
    _expected_price_required = models.Constraint(
        'CHECK (expected_price IS NOT NULL)',
        'Expected price is required',
    )