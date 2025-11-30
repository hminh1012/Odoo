# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
from markupsafe import Markup


class SchoolTransportController(http.Controller):
    
    @http.route('/school_transport/map/<int:route_id>', type='http', auth='user', website=True)
    def transport_map(self, route_id, **kwargs):
        """Render the interactive map for a transport route."""
        route = request.env['school.transport.route'].browse(route_id)
        
        if not route.exists():
            return request.render('at_school_management.transport_map_error', {
                'error': 'Route not found'
            })
        
        # Get map data
        map_data = route.get_map_data()
        
        return request.render('at_school_management.transport_map_template', {
            'route': route,
            'map_data': Markup(json.dumps(map_data)),
            'center_lat': route.map_center_lat or 16.0544,
            'center_lon': route.map_center_lon or 108.2022,
        })
    
    @http.route('/school_transport/api/route/<int:route_id>', type='json', auth='user')
    def get_route_data(self, route_id, **kwargs):
        """API endpoint to get route data as JSON."""
        route = request.env['school.transport.route'].browse(route_id)
        
        if not route.exists():
            return {'error': 'Route not found'}
        
        return route.get_map_data()

    @http.route('/school_transport/api/checkin', type='http', auth='public', methods=['POST'], csrf=False)
    def iot_checkin(self, **kwargs):
        """
        Receive IoT Check-in Data.
        Payload: {
            "card_id": "UID",
            "gps_lat": 16.0,
            "gps_lon": 108.0,
            "timestamp": "2025-11-28 14:00:00"
        }
        """
        # 1. Extract Data
        try:
            data = json.loads(request.httprequest.data)
        except json.JSONDecodeError:
            return request.make_response(
                json.dumps({'status': 'error', 'message': 'Invalid JSON'}),
                headers={'Content-Type': 'application/json'}
            )
            
        card_id = data.get('card_id')
        gps_lat = data.get('gps_lat')
        gps_lon = data.get('gps_lon')
        timestamp = data.get('timestamp')

        if not card_id:
            return request.make_response(
                json.dumps({'status': 'error', 'message': 'Missing card_id'}),
                headers={'Content-Type': 'application/json'}
            )

        # 2. Find Student Card
        card = request.env['school.student.card'].sudo().search([('card_id', '=', card_id)], limit=1)
        
        # 3. Prepare Log Data
        log_vals = {
            'card_id': card_id,
            'timestamp': timestamp or fields.Datetime.now(),
            'gps_lat': gps_lat,
            'gps_lon': gps_lon,
            'event_type': 'check_in', # Default to check-in for now
        }

        response_data = {}
        if card:
            # Valid Student
            log_vals.update({
                'student_id': card.student_id.id,
                'status': 'success',
                'message': f'Student {card.student_id.name} checked in.',
            })
            request.env['school.transport.trip.log'].sudo().create(log_vals)
            response_data = {
                'status': 'success',
                'student_name': card.student_id.name,
                'student_id': card.student_id.id
            }
        else:
            # Invalid Card
            log_vals.update({
                'status': 'denied',
                'message': 'Card not registered.',
            })
            request.env['school.transport.trip.log'].sudo().create(log_vals)
            response_data = {'status': 'error', 'message': 'Card not found'}
            
        return request.make_response(
            json.dumps(response_data),
            headers={'Content-Type': 'application/json'}
        )

    @http.route('/school', type='http', auth='public', website=True)
    def school_routes(self, **kwargs):
        """Display list of all school bus routes."""
        routes = request.env['school.transport.route'].sudo().search([])
        return request.render('at_school_management.school_routes_page_new', {
            'routes': routes
        })
