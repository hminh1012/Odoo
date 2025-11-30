{
    'name': 'Bus Attendance System',
    'version': '1.0',
    'summary': 'Manage student pickup and dropoff using face recognition',
    'author': 'Your Name',
    'category': 'Education',
    'depends': ['base', 'at_school_management'],
    'data': [
       'security/ir.model.access.csv',  
	'views/transport_log_view.xml',
    ],
    'installable': True,
    'application': True,
}