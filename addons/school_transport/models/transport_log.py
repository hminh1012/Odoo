from odoo import models, fields

class TransportLog(models.Model):
    _name = 'transport.log'
    _description = 'Transport Log'
    _order = 'create_date desc' # Newest first

    student_id = fields.Many2one('school.student', string='Student', required=True)
    vehicle_id = fields.Char(string='Vehicle Plate')
    student_code = fields.Char(related='student_id.admission_no', string='Student Code')
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now)
    gps_location = fields.Char(string='GPS Coordinates')
    image = fields.Binary(string='Evidence Image')
    type = fields.Selection([
        ('pickup', 'Pick Up'),
        ('dropoff', 'Drop Off')
    ], string='Status', default='pickup')