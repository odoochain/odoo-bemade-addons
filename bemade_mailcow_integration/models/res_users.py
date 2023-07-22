from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    mailcow_mailbox = fields.Boolean(string='Mailcow Mailbox', default=False)

    @api.model
    def create(self, vals):
        res = super(ResUsers, self).create(vals)

        if vals.get('mailcow_mailbox', false):
            self.env['mail.mailcow.mailbox'].create_mailbox_for_user(res)

        return res
