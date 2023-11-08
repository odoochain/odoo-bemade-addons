from odoo import models, fields, _, api, Command
from odoo.exceptions import ValidationError
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class Patient(models.Model):
    _name = 'sports.patient'
    _description = "Patient at a sports medicine clinic."
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'last_name, first_name'

    first_name = fields.Char(required=True, tracking=True)
    last_name = fields.Char(required=True, tracking=True)
    name = fields.Char(compute="_compute_name")
    date_of_birth = fields.Date(
        groups="bemade_sports_clinic.group_sports_clinic_treatment_professional",
        tracking=True)
    age = fields.Integer(compute='_compute_age',
                         groups="bemade_sports_clinic.group_sports_clinic_treatment_professional",
                         tracking=True)
    mobile = fields.Char(unaccent=False,
                        groups="bemade_sports_clinic.group_sports_clinic_user",
                        tracking=True)
    email = fields.Char(groups="bemade_sports_clinic.group_sports_clinic_user",
                        tracking=True)
    contact_ids = fields.One2many(comodel_name='sports.patient.contact',
                                  inverse_name='patient_id',
                                  string='Patient Contacts',
                                  groups="bemade_sports_clinic.group_sports_clinic_user")
    team_ids = fields.Many2many(comodel_name='sports.team',
                                relation='sports_team_patient_rel',
                                column1='patient_id',
                                column2='team_id',
                                string='Teams', )
    match_status = fields.Selection([  # Selection for easy expansion later
        ('yes', 'Yes'),
        ('no', 'No'),
    ], required=True, default='yes', tracking=True)
    practice_status = fields.Selection([
        ('yes', 'Yes'),
        ('no_contact', 'Yes, no contact'),
        ('no', 'No')], tracking=True, required=True, default='yes')

    injury_ids = fields.One2many(comodel_name='sports.patient.injury',
                                 inverse_name='patient_id',
                                 string='Injuries', )
    injured_since = fields.Date(compute='_compute_is_injured')
    predicted_return_date = fields.Date(tracking=True)
    return_date = fields.Date(tracking=True,
                              help="When the player was cleared by medical staff to "
                                   "return to match play.")
    is_injured = fields.Boolean(compute="_compute_is_injured")
    stage = fields.Selection(
        selection=[('no_play', 'Injured'), ('practice_ok', 'Cleared for Practice'), ('healthy', 'Cleared to Play')],
        compute='_compute_stage')
    last_consultation_date = fields.Date()
    active_injury_count = fields.Integer(compute='_compute_active_injury_count')

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'team_ids' in fields_list and 'params' in self.env.context \
                and self.env.context.get('params')['model'] == 'sports.team':
            team = self.env['sports.team'].browse(self.env.context.get('params')['id'])
            team_ids = [Command.set([team.id])]
            if team_ids:
                res.update({'team_ids': team_ids})
        return res

    @api.constrains('match_status', 'practice_status')
    def constrain_match_and_practice_status(self):
        """ Avoid invalid combinations of match and practice status:
                - Yes (match), No (practice)
                - Yes (match), No Contact (practice)
        """
        # combinations of (match_status, practice_status) that are valid
        valid_combinations = [('yes', 'yes'), ('no', 'yes'), ('no', 'no_contact'), ('no', 'no')]
        for rec in self:
            if (rec.match_status, rec.practice_status) not in valid_combinations:
                raise ValidationError(_("Invalid combination of match and practice status."))

    @api.depends('injury_ids.stage')
    def _compute_active_injury_count(self):
        for rec in self:
            rec.active_injury_count = len(rec.injury_ids.filtered(lambda r: r.stage == 'active'))

    @api.depends('match_status', 'practice_status')
    def _compute_stage(self):
        stage_map = {
            ('yes', 'yes'): 'healthy',
            ('no', 'yes'): 'practice_ok',
            ('no', 'no_contact'): 'practice_ok',
            ('no', 'no'): 'no_play',
        }
        for rec in self:
            if (rec.match_status, rec.practice_status) not in stage_map:
                rec.stage = False  # not a valid combination, will be caught by constraint if save is attempted
                continue
            rec.stage = stage_map[(rec.match_status, rec.practice_status)]

    @api.depends('date_of_birth')
    def _compute_age(self):
        for rec in self:
            if not rec.date_of_birth:
                rec.age = False
            else:
                rec.age = relativedelta(date.today(), rec.date_of_birth).years

    @api.depends('first_name', 'last_name')
    def _compute_name(self):
        for rec in self:
            rec.name = ((rec.first_name or "") + " " + (rec.last_name or
                                                        "")).strip()

    @api.depends('practice_status', 'match_status', 'injury_ids.injury_date_time')
    def _compute_is_injured(self):
        for rec in self:
            rec.is_injured = rec.practice_status != 'yes' or rec.match_status != 'yes'
            if rec.is_injured:
                unresolved_injuries = rec.injury_ids.filtered(lambda r: not r.stage == 'resolved')
                rec.injured_since = unresolved_injuries and unresolved_injuries[0].injury_date_time
            else:
                rec.injured_since = False

    def action_view_patient_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sports.patient',
            'res_id': self.id,
            'context': self._context,
        }

    def action_consulted_today(self):
        self.ensure_one()  # should just be called from form view
        self.last_consultation_date = date.today()
        return {
            'view_mode': 'form',
            'res_model': 'sports.patient',
            'context': self._context,
            'res_id': self.id,
        }


class PatientContact(models.Model):
    _name = 'sports.patient.contact'
    _description = "Emergency or other contacts for a patient."

    sequence = fields.Integer(required=True, default=0)
    name = fields.Char(unaccent=False)
    contact_type = fields.Selection(selection=[
        ('mother', 'Mother'),
        ('father', 'Father'),
        ('other', 'Other'),
    ], required=True)
    mobile = fields.Char(unaccent=False, required=True)
    patient_id = fields.Many2one(comodel_name='sports.patient', string='Patient')


class PatientInjury(models.Model):
    _name = 'sports.patient.injury'
    _description = "A patient's injury."
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'diagnosis'

    patient_id = fields.Many2one(comodel_name='sports.patient',
                                 string="Patient",
                                 readonly=True,
                                 required=True)
    patient_name = fields.Char(related="patient_id.name")
    diagnosis = fields.Char(tracking=True)
    injury_date_time = fields.Datetime(string='Date and Time of Injury', required=True,
                                       default=datetime.now())
    internal_notes = fields.Html(tracking=True)
    external_notes = fields.Html(tracking=True)
    treatment_professional_ids = fields.Many2many(comodel_name='res.users',
                                                  relation='patient_injury_treatment_pro_rel',
                                                  column1='patient_injury_id',
                                                  column2='treatment_pro_id',
                                                  string='Treatment Professionals',
                                                  domain=[
                                                      ('is_treatment_professional', '=',
                                                       True)], tracking=True)
    predicted_resolution_date = fields.Date(tracking=True)
    resolution_date = fields.Date(tracking=True,
                                  help="The date when the injury was actually resolved.")
    stage = fields.Selection(selection=[('active', 'Active'), ('resolved', 'Resolved')], compute='_compute_stage')

    @api.depends('resolution_date')
    def _compute_stage(self):
        for rec in self:
            if rec.resolution_date and rec.resolution_date <= date.today():
                rec.stage = 'resolved'
            else:
                rec.stage = 'active'

    def write(self, vals):
        super().write(vals)
        if 'treatment_professional_ids' in vals:
            to_subscribe = (self.treatment_professional_ids.mapped('partner_id')
                            - self.message_follower_ids.mapped('partner_id'))
            self.message_subscribe(to_subscribe.ids)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            to_subscribe = (rec.treatment_professional_ids.mapped('partner_id')
                            - rec.message_follower_ids.mapped('partner_id'))
            rec.message_subscribe(to_subscribe.ids)
        return res

    def action_view_injury_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sports.patient.injury',
            'res_id': self.id,
            'context': self._context,
        }
