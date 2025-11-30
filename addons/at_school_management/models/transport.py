from odoo import models, fields, api, _
import logging
import json
import math

_logger = logging.getLogger(__name__)

class TransportRoute(models.Model):
    _name = 'school.transport.route'
    _description = 'Transport Route'

    name = fields.Char(string="Route Name", required=True)
    bus_number = fields.Char(string="Bus Number")
    driver_name = fields.Char(string="Driver Name")
    capacity = fields.Integer(string="Seating Capacity", default=40)
    student_ids = fields.Many2many('school.student', string="Assigned Students")
    stop_ids = fields.One2many('school.transport.stop', 'route_id', string="Route Stops")
    
    # Map and Route Geometry Fields
    route_geometry = fields.Text(string="Route Geometry (JSON)", help="JSON array of [lat, lon] coordinates forming the route path")
    total_distance = fields.Float(string="Total Distance (km)", compute='_compute_total_distance', store=True)
    map_center_lat = fields.Float(string="Map Center Latitude", compute='_compute_map_center', store=True)
    map_center_lon = fields.Float(string="Map Center Longitude", compute='_compute_map_center', store=True)
    route_map_html = fields.Html(string="Route Map HTML", compute='_compute_route_map_html', sanitize=False)


    def _compute_route_map_html(self):
        for route in self:
            if route.id:
                route.route_map_html = f'<iframe style="width: 100%; height: 100%; border: none; border-radius: 8px;" src="/school_transport/map/{route.id}"></iframe>'
            else:
                route.route_map_html = '<p>Save the record to view the map.</p>'
    
    @api.depends('stop_ids.latitude', 'stop_ids.longitude')
    def _compute_map_center(self):
        """Compute the center point of the route for map display."""
        for route in self:
            stops_with_coords = route.stop_ids.filtered(lambda s: s.latitude != 0.0 and s.longitude != 0.0)
            if stops_with_coords:
                route.map_center_lat = sum(s.latitude for s in stops_with_coords) / len(stops_with_coords)
                route.map_center_lon = sum(s.longitude for s in stops_with_coords) / len(stops_with_coords)
            else:
                # Default to Danang, Vietnam
                route.map_center_lat = 16.0544
                route.map_center_lon = 108.2022
    
    @api.depends('stop_ids.latitude', 'stop_ids.longitude', 'stop_ids.sequence')
    def _compute_total_distance(self):
        """Calculate total route distance based on stop coordinates."""
        for route in self:
            total = 0.0
            ordered_stops = route.stop_ids.sorted(key=lambda s: s.sequence)
            stops_with_coords = [s for s in ordered_stops if s.latitude != 0.0 and s.longitude != 0.0]
            
            for i in range(len(stops_with_coords) - 1):
                stop1 = stops_with_coords[i]
                stop2 = stops_with_coords[i + 1]
                total += self._haversine_distance(
                    stop1.latitude, stop1.longitude,
                    stop2.latitude, stop2.longitude
                )
            route.total_distance = round(total, 2)
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula."""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def compute_route_geometry(self):
        """Generate route geometry from ordered stops."""
        for route in self:
            ordered_stops = route.stop_ids.sorted(key=lambda s: s.sequence)
            stops_with_coords = [s for s in ordered_stops if s.latitude != 0.0 and s.longitude != 0.0]
            
            if stops_with_coords:
                geometry = [[s.latitude, s.longitude] for s in stops_with_coords]
                route.route_geometry = json.dumps(geometry)
            else:
                route.route_geometry = '[]'
    
    def get_map_data(self):
        """Prepare data for map widget display."""
        self.ensure_one()
        ordered_stops = self.stop_ids.sorted(key=lambda s: s.sequence)
        
        stops_data = []
        for stop in ordered_stops:
            if stop.latitude != 0.0 and stop.longitude != 0.0:
                stops_data.append({
                    'name': stop.name,
                    'lat': stop.latitude,
                    'lon': stop.longitude,
                    'arrival_time': stop.arrival_time,
                    'departure_time': stop.departure_time,
                    'sequence': stop.sequence,
                })
        
        return {
            'route_name': self.name,
            'bus_number': self.bus_number,
            'stops': stops_data,
            'center_lat': self.map_center_lat,
            'center_lon': self.map_center_lon,
            'total_distance': self.total_distance,
        }


class TransportStop(models.Model):
    _name = 'school.transport.stop'
    _description = 'Route Stop'
    _order = 'route_id, sequence, id'

    name = fields.Char(string="Stop Name", required=True)
    sequence = fields.Integer(string="Sequence", default=10, help="Order of this stop in the route")
    arrival_time = fields.Float(string="Arrival Time (HH.MM)")
    departure_time = fields.Float(string="Departure Time (HH.MM)")
    route_id = fields.Many2one('school.transport.route', string="Transport Route", ondelete='cascade')
    
    # Geocoding Fields (renamed for consistency)
    latitude = fields.Float(string="Latitude", digits=(10, 7), readonly=True)
    longitude = fields.Float(string="Longitude", digits=(10, 7), readonly=True)
    
    # Keep old field names for backward compatibility
    x_lat = fields.Float(related='latitude', string="X Latitude (deprecated)", readonly=True, store=False)
    x_lon = fields.Float(related='longitude', string="X Longitude (deprecated)", readonly=True, store=False)

    def geocode_record(self):
        """Button-callable method to geocode a single stop."""
        service = self.env['schoolbus.osm']
        for stop in self:
            if not stop.name:
                stop.write({'latitude': 0.0, 'longitude': 0.0})
                continue
            
            try:
                # Focus on Danang, Vietnam for better geocoding accuracy
                results = service._osm_geocode(
                    street=stop.name,
                    city='Danang',
                    country='Vietnam',
                    limit=1
                )
                if results:
                    stop.write({
                        'latitude': float(results[0].get('lat', 0.0)),
                        'longitude': float(results[0].get('lon', 0.0)),
                    })
                    _logger.info(f"Geocoded stop {stop.name}: {stop.latitude}, {stop.longitude}")
                else:
                    stop.write({'latitude': 0.0, 'longitude': 0.0})
                    _logger.warning(f"No geocoding results for stop: {stop.name}")
            except Exception as e:
                _logger.error(f"Geocoding failed for stop {stop.name}: {e}")
                stop.write({'latitude': 0.0, 'longitude': 0.0})

    def _run_geocode_cron(self):
        """Called by cron job to geocode stops with missing coordinates."""
        _logger.info("Running geocoding cron job for transport stops...")
        stops_to_geocode = self.search([
            '|', ('latitude', '=', 0.0), ('longitude', '=', 0.0),
            ('name', '!=', False)
        ], limit=100)
        
        _logger.info(f"Found {len(stops_to_geocode)} stops to geocode.")
        stops_to_geocode.geocode_record()