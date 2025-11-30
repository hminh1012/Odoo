from odoo import http, fields
from odoo.http import request
import logging
from datetime import datetime, time, timedelta

_logger = logging.getLogger(__name__)

class AttendanceController(http.Controller):

    def _get_todays_attendance(self):
        # Fetch logs from the last 24 hours to avoid timezone issues
        time_threshold = fields.Datetime.now() - timedelta(hours=24)
        _logger.info(f"Searching logs created after {time_threshold}")
        logs = request.env['transport.log'].sudo().search([
            ('create_date', '>=', time_threshold)
        ], order='create_date desc')
        _logger.info(f"Found {len(logs)} logs")
        return logs

    @http.route('/attendance', type='http', auth='public', website=True)
    def attendance_form(self, **kw):
        logs = self._get_todays_attendance()
        return request.render('school_attendance_web.attendance_form', {
            'attendance_logs': logs
        })

    @http.route('/attendance/submit', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def attendance_submit(self, **kw):
        student_code = kw.get('student_code')
        logs = self._get_todays_attendance()
        
        if not student_code:
            return request.render('school_attendance_web.attendance_form', {
                'error': 'Please enter a student code.',
                'attendance_logs': logs
            })

        # Find student
        student = request.env['school.student'].sudo().search([('admission_no', '=', student_code)], limit=1)

        if not student:
            return request.render('school_attendance_web.attendance_form', {
                'error': 'Student not found.',
                'student_code': student_code,
                'attendance_logs': logs
            })

        # Create log
        try:
            request.env['transport.log'].sudo().create({
                'student_id': student.id,
                'vehicle_id': 'WEB-INTERFACE',
                'type': 'pickup', # Default to pickup for now
                'gps_location': 'Web Interface'
            })
            # Refresh logs to include the new one
            logs = self._get_todays_attendance()
            return request.render('school_attendance_web.attendance_form', {
                'success': f'Attendance recorded for {student.name}.',
                'attendance_logs': logs
            })
        except Exception as e:
            _logger.error(f"Error recording attendance: {e}")
            return request.render('school_attendance_web.attendance_form', {
                'error': 'An error occurred while recording attendance.',
                'attendance_logs': logs
            })
