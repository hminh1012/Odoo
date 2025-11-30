# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class SchoolGeocodeWizard(models.TransientModel):
    _name = 'school.geocode.wizard'
    _description = 'Geocoding Wizard'

    # Helper fields for the view
    active_ids_count = fields.Integer(
        compute='_compute_active_context',
        string="Number of records"
    )
    active_model_name = fields.Char(
        compute='_compute_active_context',
        string="Model Name"
    )

    @api.depends('active_ids_count', 'active_model_name')
    def _compute_active_context(self):
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids', [])
        
        model_name = ''
        if active_model:
            model_data = self.env['ir.model'].search([('model', '=', active_model)], limit=1)
            model_name = model_data.name or active_model
            
        for record in self:
            record.active_ids_count = len(active_ids)
            record.active_model_name = model_name

    def action_geocode_records(self):
        """
        Geocodes all records passed in the context (from a list view).
        """
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids', [])
        
        if not active_model or not active_ids:
            return {'type': 'ir.actions.act_window_close'}

        _logger.info(f"Geocode wizard running on model {active_model} for IDs {active_ids}")
        
        records = self.env[active_model].browse(active_ids)
        
        if hasattr(records, 'geocode_record'):
            records.geocode_record()
        else:
            _logger.warning(f"Model {active_model} does not have a 'geocode_record' method.")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Geocoding Complete"),
                'message': _("%s records have been processed.", len(active_ids)),
                'type': 'success',
                'sticky': False,
            }
        }