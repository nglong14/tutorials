from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class EstatePropertyTag(models.Model):
    _name = 'estate.property.tag'
    _description = 'Real Estate Property Tag'
    _order = 'name'

    name = fields.Char(required=True)
    color = fields.Integer()

    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'Tag name must be unique',
    )


class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Estate Property'
    _order = 'id desc'

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
        store=True,
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
    property_type_id = fields.Many2one('estate.property.type', string='Property Type')
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

    @api.constrains('expected_price', 'selling_price')
    def _check_selling_price(self):
        for prop in self:
            if not prop.selling_price:
                continue
            if prop.selling_price < 0.9 * prop.expected_price:
                raise ValidationError(
                    _("The selling price cannot be lower than 90%% of the expected price.")
                )

    @api.onchange('garden')
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = False
            self.garden_orientation = False

    def action_cancel(self):
        for prop in self:
            if prop.state == 'sold':
                raise UserError(_("Sold properties cannot be cancelled."))
        self.write({'state': 'cancelled'})

    def action_sold(self):
        for prop in self:
            if prop.state == 'cancelled':
                raise UserError(_("Cancelled properties cannot be sold."))
        self.write({'state': 'sold'})

    @api.ondelete(at_uninstall=False)
    def _unlink_except_new_or_cancelled(self):
        if any(prop.state not in ('new', 'cancelled') for prop in self):
            raise UserError(_("Only properties in 'New' or 'Cancelled' state can be deleted."))

    _name_required = models.Constraint(
        'CHECK (name IS NOT NULL)',
        'Name is required',
    )
    _expected_price_positive = models.Constraint(
        'CHECK (expected_price > 0)',
        'The expected price must be strictly positive',
    )
    _selling_price_positive = models.Constraint(
        'CHECK (selling_price >= 0)',
        'The selling price must be positive',
    )