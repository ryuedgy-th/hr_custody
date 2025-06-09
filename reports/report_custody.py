from odoo import fields, models, tools


class ReportCustody(models.Model):
    _name = "report.custody"
    _description = "Custody Analysis"
    _auto = False
    _order = 'name desc'

    name = fields.Char(string='Code',
                       help='A unique code associated with the custody report')
    date_request = fields.Date(string='Requested Date',
                               help='Choose the Request date')
    employee_id = fields.Many2one('hr.employee', string='Select Employee',
                                  help='Select the employee associated '
                                       'with this record.')
    purpose = fields.Char(string='Reason',
                          help='Enter the reason for this record')
    custody_property_id = fields.Many2one('custody.property',
                                          help='Select the property associated'
                                               ' with this record.',
                                          string='Property Name')

    # ⭐ NEW: Approved By field
    approved_by_id = fields.Many2one('res.users', string='Approved By',
                                     help='User who approved this custody')
    approved_date = fields.Datetime(string='Approved Date',
                                    help='When this request was approved')

    return_date = fields.Date(string='Return Date',
                              help='The date when the custody is expected to '
                                   'be returned.')
    renew_date = fields.Date(string='Renewal Return Date',
                             help='The date when the custody is renewed and '
                                  'expected to be returned.')
    is_renew_return_date = fields.Boolean(string='Renewal Return Date',
                                          help='Indicates whether there is a '
                                               'renewal return date or not.')
    state = fields.Selection(
        [('draft', 'Draft'), ('to_approve', 'Waiting For Approval'),
         ('approved', 'Approved'),
         ('returned', 'Returned'), ('rejected', 'Refused')], string='Status',
        help='The current status of the record')

    def _select(self):
        """the function used to construct the
        SELECT statement for retrieving specific fields in a SQL query."""
        select_str = """
             SELECT
                    (select 1 ) AS nbr,
                    t.id as id,
                    t.name as name,
                    t.date_request as date_request,
                    t.employee_id as employee,
                    t.purpose as purpose,
                    t.custody_property_id as custody_name,
                    t.approved_by_id as approved_by_id,
                    t.approved_date as approved_date,
                    t.return_date as return_date,
                    t.renew_date as renew_date,
                    t.is_renew_return_date as renew_return_date,
                    t.state as state
        """
        return select_str

    def _group_by(self):
        """The function used to construct
        the GROUP BY clause for grouping fields in a SQL query."""
        group_by_str = """
                GROUP BY
                    t.id,
                    name,
                    date_request,
                    employee_id,
                    purpose,
                    custody_property_id,
                    approved_by_id,
                    approved_date,
                    return_date,
                    renew_date,
                    is_renew_return_date,
                    state
        """
        return group_by_str

    def init(self):
        """The function used to initialize the
        database view 'report_custody' for reporting purposes."""
        tools.sql.drop_view_if_exists(self._cr, 'report_custody')
        self._cr.execute("""
            CREATE view report_custody as
              %s
              FROM hr_custody t
                %s
        """ % (self._select(), self._group_by()))
