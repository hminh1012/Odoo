from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class Student(models.Model):
    _name = 'school.student'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Student Record'

    name = fields.Char(string="Full Name", required=True, tracking=True)
    admission_no = fields.Char(string="Admission No", required=True, unique=True, tracking=True)
    dob = fields.Date(string="Date of Birth", required=True,)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string="Gender", required=True,)
    medical_history = fields.Text(string="Medical History")
    parent_id = fields.Many2one('school.parent', string="Parent/Guardian")
    class_id = fields.Many2one('school.class', string="Class", required=True, tracking=True)
    document_ids = fields.One2many('school.student.document', 'student_id', string="Documents")
    blood_group = fields.Selection([
        ('O-', 'O-'),
        ('O+', 'O+'),
        ('A-', 'A-'),
        ('A+', 'A+'),
        ('B-', 'B-'),
        ('B+', 'B+'),
        ('AB-', 'AB-'),
        ('AB+', 'AB+')
    ], string="Blood group", required=True,)
    is_student = fields.Boolean(string="Is Student", default=True)
    roll_no = fields.Char(string="Roll No", unique=True, required=True)
    house_address = fields.Text(string="Home Address", required=True)
    doj = fields.Date(string="Date of joining", required=True)
    trackskill = fields.Text(string="Track Skills")
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")

    # 👇 New field for uploading and storing student image
    image_1920 = fields.Image(string="Student Photo", max_width=1920, max_height=1920, store=True)

    # --- NEW GEOCODING FIELDS ---
    x_lat = fields.Float(string="Latitude", digits=(10, 7), readonly=True)
    x_lon = fields.Float(string="Longitude", digits=(10, 7), readonly=True)

    # --- NEW GEOCODING METHODS ---
    def geocode_record(self):
        """Button-callable method to geocode a single student's address."""
        service = self.env['schoolbus.osm']
        for student in self:
            if not student.house_address:
                student.write({'x_lat': 0.0, 'x_lon': 0.0})
                continue
            
            try:
                results = service._osm_geocode(
                    street=student.house_address,
                    city='Danang',
                    country='Vietnam',
                    limit=1
                )
                if results:
                    student.write({
                        'x_lat': float(results[0].get('lat', 0.0)),
                        'x_lon': float(results[0].get('lon', 0.0)),
                    })
                    _logger.info(f"Geocoded student {student.name}: {student.x_lat}, {student.x_lon}")
                else:
                    student.write({'x_lat': 0.0, 'x_lon': 0.0})
            except Exception as e:
                _logger.error(f"Geocoding failed for student {student.name}: {e}")
                student.write({'x_lat': 0.0, 'x_lon': 0.0})

    def _run_geocode_cron(self):
        """Called by cron job to geocode students with missing coordinates."""
        _logger.info("Running geocoding cron job for students...")
        # Process in batches of 100 to avoid timeouts
        students_to_geocode = self.search([
            '|', ('x_lat', '=', 0.0), ('x_lon', '=', 0.0),
            ('house_address', '!=', False)
        ], limit=100)
        
        _logger.info(f"Found {len(students_to_geocode)} students to geocode.")
        students_to_geocode.geocode_record()