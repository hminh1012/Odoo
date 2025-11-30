from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class TransportController(http.Controller):
    
    # Đây là địa chỉ cái "Cửa sổ": /api/transport/attendance
    # csrf=False: Để cho phép thiết bị bên ngoài gửi dữ liệu vào mà không bị chặn bảo mật
    @http.route('/api/transport/attendance', type='json', auth='public', methods=['POST'], csrf=False)
    def receive_attendance(self, **rec):
        _logger.info(f"Received attendance data: {rec}")
        # 1. Lấy dữ liệu gửi lên
        student_code = rec.get('student_code')
        vehicle_id = rec.get('vehicle_id')
        gps = rec.get('gps')
        image = rec.get('image')
        log_type = rec.get('type', 'pickup') # Mặc định là pickup (lên xe)

        # 2. Tìm học sinh có mã số này trong Database
        # .sudo() nghĩa là "dùng quyền Admin" để tìm (vì thiết bị bên ngoài không có login)
        student = request.env['school.student'].sudo().search([('admission_no', '=', student_code)], limit=1)

        if student:
            _logger.info(f"Student found: {student.name} (ID: {student.id})")
            # 3. Nếu tìm thấy -> Tạo dòng nhật ký mới
            new_log = request.env['transport.log'].sudo().create({
                'student_id': student.id,
                'vehicle_id': vehicle_id,
                'gps_location': gps,
                'image': image,
                'type': log_type
            })
            _logger.info(f"Created transport log: {new_log.id}")
            return {'status': 'success', 'message': f'Attendance recorded: {student.name}'}
        
        else:
            # 4. Nếu không tìm thấy
            _logger.warning(f"Student not found for code: {student_code}")
            return {'status': 'error', 'message': 'Student code not found'}