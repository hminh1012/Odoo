# -*- coding: utf-8 -*-
import requests
import logging
from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
GEOCODE_ENDPOINT = 'https://nominatim.openstreetmap.org/search'

class OsmService(models.AbstractModel):
    """
    Abstract model to provide geocoding services using OpenStreetMap Nominatim.
    """
    _name = 'schoolbus.osm'
    _description = 'OpenStreetMap Geocoding Service'

    def _osm_geocode(self, street=None, city=None, state=None, country=None, postalcode=None, limit=1):
        """
        Geocodes a structured address to latitude and longitude.
        """
        if not any([street, city, state, country, postalcode]):
            _logger.warning("Geocoding called with all empty parameters.")
            return []

        params = {
            'street': street,
            'city': city,
            'state': state,
            'country': country,
            'postalcode': postalcode,
            'format': 'json',
            'limit': limit,
            'addressdetails': 1,
        }
        query_params = {k: v for k, v in params.items() if v}

        try:
            headers = {'User-Agent': 'Odoo (http://www.odoo.com)'}
            response = requests.get(GEOCODE_ENDPOINT, params=query_params, headers=headers, timeout=10)
            response.raise_for_status()
            results = response.json()
            
            if not results:
                return []
                
            return [{
                'lat': res.get('lat'),
                'lon': res.get('lon'),
            } for res in results]

        except requests.exceptions.RequestException as e:
            _logger.error("OSM geocoding request failed: %s", e)
            return []