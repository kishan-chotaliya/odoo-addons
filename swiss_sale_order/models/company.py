from odoo import api, fields, models, _

class ResCompany(models.Model):
	_inherit = 'res.company'

	roc = fields.Char(string='ROC')
	hdb_no = fields.Char(string='Registered HDB No')