from odoo import models, fields, api

class StudentCard(models.Model):
    _name = 'school.student.card'
    _description = 'Student RFID Card'
    _rec_name = 'card_id'

    card_id = fields.Char(string="Card UID", required=True, unique=True, help="Unique Identifier from the RFID card")
    student_id = fields.Many2one('school.student', string="Student", required=True, help="Student assigned to this card")
    active = fields.Boolean(default=True, string="Active")
    issued_date = fields.Date(string="Issued Date", default=fields.Date.today)
    status = fields.Selection([
        ('active', 'Active'),
        ('lost', 'Lost'),
        ('expired', 'Expired')
    ], string="Status", default='active')

class TripLog(models.Model):
    _name = 'school.transport.trip.log'
    _description = 'Transport Trip Log'
    _order = 'timestamp desc'

    student_id = fields.Many2one('school.student', string="Student")
    card_id = fields.Char(string="Card UID Used") # For logs where student might not be found or card is invalid
    route_id = fields.Many2one('school.transport.route', string="Route")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    timestamp = fields.Datetime(string="Time", default=fields.Datetime.now, required=True)
    gps_lat = fields.Float(string="Latitude", digits=(10, 7))
    gps_lon = fields.Float(string="Longitude", digits=(10, 7))
    event_type = fields.Selection([
        ('check_in', 'Check In'),
        ('check_out', 'Check Out')
    ], string="Event Type", default='check_in')
    status = fields.Selection([
        ('success', 'Success'),
        ('denied', 'Denied'),
        ('error', 'Error')
    ], string="Status", default='success')
    message = fields.Char(string="Log Message")

class TransportRoute(models.Model):
    _inherit = 'school.transport.route'

    vehicle_id = fields.Many2one('fleet.vehicle', string="Assigned Vehicle")
