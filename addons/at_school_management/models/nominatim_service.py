# -*- coding: utf-8 -*-
import requests
import logging
from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Nominatim API endpoints
GEOCODE_ENDPOINT = 'https://nominatim.openstreetmap.org/search'
REVERSE_GEOCODE_ENDPOINT = 'https://nominatim.openstreetmap.org/reverse'

class NominatimService(models.AbstractModel):
    """
    Abstract model to provide geocoding services using OpenStreetMap Nominatim.
    """
    _name = 'nominatim.geocoding.service'
    _description = 'Nominatim Geocoding Service'

    def _nominatim_geocode(self, street=None, city=None, state=None, country=None, postalcode=None, limit=1):
        """
        Geocodes a structured address to latitude and longitude.
        """
        if not any([street, city, country, postalcode]):
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
        
        # Filter out None values from parameters
        query_params = {k: v for k, v in params.items() if v}

        try:
            # Nominatim requires a descriptive User-Agent
            headers = {'User-Agent': 'Odoo (http://www.odoo.com)'}
            response = requests.get(GEOCODE_ENDPOINT, params=query_params, headers=headers, timeout=10)
            response.raise_for_status()  # Raise HTTPError for bad responses
            
            results = response.json()
            
            if not results:
                return []
                
            return [{
                'lat': res.get('lat'),
                'lon': res.get('lon'),
                'display_name': res.get('display_name'),
                'address': res.get('address', {})
            } for res in results]

        except requests.exceptions.RequestException as e:
            _logger.error("Nominatim geocoding request failed: %s", e)
            # We don't raise a UserError here to not block the UI
            # You could raise UserError if geocoding is critical
            return []