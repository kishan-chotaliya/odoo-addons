from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    remarks = fields.Text()
    group_ids = fields.One2many('group.line', 'order_id', string="Groups")
    job_site = fields.Char(string="Job Site")
    final_sale_price = fields.Float(compute='_compute_final_sale_price')
    ref = fields.Many2one('sale.order')
    quote_count = fields.Integer(compute='_compute_quote_count')

    @api.multi
    def _compute_quote_count(self):
        for record in self:
            record.quote_count = self.search_count([('ref', 'child_of', self.id)])

    @api.depends('group_ids.total_sale')
    def _compute_final_sale_price(self):
        for record in self:
            for line in record.group_ids:
                record.final_sale_price += line.total_sale

    @api.multi
    def copy(self):
        res = super(SaleOrder, self).copy()
        res.origin = self.name
        res.ref = self.id
        return res

    @api.multi
    def quotation_history(self):
        all_quote = self.search([('ref', 'child_of', self.id)])
        action = self.env.ref('sale.action_quotations').read()[0]
        if len(all_quote) >= 1:
            action['domain'] = [('id', 'in', all_quote.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
        


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    group_order_line_id = fields.Many2one('group.order.line.line')

class GroupLine(models.Model):
    _name = 'group.line'

    order_id = fields.Many2one('sale.order')
    title = fields.Char(required=True)
    order_line_ids = fields.One2many('group.order.line', 'group_line_id', string="Group Order Lines")
    total_sale = fields.Float(compute='_compute_sale_total', string='Sale Price Total')
    total_cost = fields.Float(compute='_compute_cost_total', string='Cost Price Total')
    total_margin = fields.Float(compute='_compute_margin_total', string='Margin Total')

    @api.depends('order_line_ids.difference')
    def _compute_margin_total(self):
        for record in self:
            for line in record.order_line_ids:
                record.total_margin += line.difference

    @api.depends('order_line_ids.cost_price')
    def _compute_cost_total(self):
        for record in self:
            for line in record.order_line_ids:
                record.total_cost += line.cost_price

    @api.depends('order_line_ids.total_sale_price')
    def _compute_sale_total(self):
        for record in self:
            for line in record.order_line_ids:
                record.total_sale += line.total_sale_price


class GroupOrderLine(models.Model):
    _name = 'group.order.line'

    group_line_id = fields.Many2one('group.line')
    product_id = fields.Many2many('product.product', compute='_compute_product_ids', string='Product Name')
    # qty = fields.Float(string="Quantity", required=True, default=1.0)
    desc = fields.Char(string='Description', required=True)
    cost_price = fields.Float(compute='_compute_cost_total')
    # sale_price_per_unit = fields.Float(related='product_id.list_price', string="Recommended Sale Price")
    total_sale_price = fields.Float(compute='_compute_sale_total', string="Total Sale Price")
    difference = fields.Float(compute='_compute_margin_total', string="Margin")
    order_line_line_ids = fields.One2many('group.order.line.line', 'group_line_line_id')

    @api.depends('order_line_line_ids.product_id')
    def _compute_product_ids(self):
        for record in self:
            product_ids = record.order_line_line_ids.mapped('product_id')
            record.product_id = product_ids.ids


    @api.depends('order_line_line_ids.difference')
    def _compute_margin_total(self):
        for record in self:
            for line in record.order_line_line_ids:
                record.difference += line.difference

    @api.depends('order_line_line_ids.cost_price')
    def _compute_cost_total(self):
        for record in self:
            for line in record.order_line_line_ids:
                record.cost_price += line.cost_price

    @api.depends('order_line_line_ids.total_sale_price')
    def _compute_sale_total(self):
        for record in self:
            for line in record.order_line_line_ids:
                record.total_sale_price += line.total_sale_price



class GroupOrderLineLine(models.Model):
    _name = 'group.order.line.line'


    group_line_line_id = fields.Many2one('group.order.line')
    product_id = fields.Many2one('product.product', required=True, string='Product Name')
    qty = fields.Float(string="Quantity", required=True, default=1.0)
    desc = fields.Char(string='Description')
    cost_price = fields.Float(compute='_compute_product_cost')
    # sale_price_per_unit = fields.Float(related='product_id.list_price', string="Recommended Sale Price")
    total_sale_price = fields.Float(string="Total Sale Price")
    difference = fields.Float(compute='_compute_diff', string="Margin")
    vendor_id = fields.Many2one('res.partner', string='Vendor', domain=[('supplier','=',True)])
    
    @api.model
    def create(self, values):
        res = super(GroupOrderLineLine, self).create(values)
        vals = {}
        order = self.env['group.order.line'].browse(values.get('group_line_line_id')).group_line_id
        product_uom = self.env['product.product'].browse(values['product_id']).uom_id.id
        # for product in values['product_id']:
        vals = {
            'product_id': values['product_id'],
            'order_id': order.order_id.id,
            'product_uom_qty': values['qty'],
            'product_uom': product_uom,
        }
        if values.get('desc'):
            vals['name'] = values['desc']

        order_line_record = self.env['sale.order.line'].create(vals)
        order_line_record.group_order_line_id = res.id
        return res
    
    @api.multi
    def write(self, values):
        res = super(GroupOrderLineLine, self).write(values)
        order_lines = self.env['sale.order.line'].search([])
        sale_orderline = order_lines.filtered(lambda x: x.group_order_line_id.id == self.id)
        if sale_orderline:
            if values.get('product_id'):
                sale_orderline.product_id = values['product_id']
            if values.get('qty'):
                sale_orderline.product_uom_qty = values['qty']
            if values.get('desc'):
                sale_orderline.name = values['desc']
        return res


    # @api.depends('sale_price_per_unit', 'qty')
    # def _compute_total_sale_price(self):
    #     for record in self:
    #         record.total_sale_price = record.sale_price_per_unit * record.qty


    @api.depends('product_id', 'qty')
    def _compute_product_cost(self):
        for record in self:
            record.cost_price = record.product_id.standard_price * record.qty

    @api.depends('cost_price', 'total_sale_price')
    def _compute_diff(self):
        for record in self:
            if record.cost_price or record.total_sale_price:
                record.difference = record.total_sale_price - record.cost_price