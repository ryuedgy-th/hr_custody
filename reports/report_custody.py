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

    # ⭐ Approval fields
    approved_by_id = fields.Many2one('res.users', string='Approved By',
                                     help='User who approved this custody')
    approved_date = fields.Datetime(string='Approved Date',
                                    help='When this request was approved')

    # ⭐ Return fields
    return_date = fields.Date(string='Expected Return Date',
                              help='The date when the custody is expected to '
                                   'be returned.')
    actual_return_date = fields.Date(string='Actual Return Date',
                                    help='When the custody was actually returned')
    returned_by_id = fields.Many2one('res.users', string='Returned By',
                                    help='User who processed the return')

    # ⭐ Performance tracking
    is_overdue = fields.Boolean(string='Was Overdue',
                               help='Whether the return was overdue')
    days_overdue = fields.Integer(string='Days Overdue',
                                 help='Number of days the return was overdue (at time of return)')

    # Renewal fields
    renew_date = fields.Date(string='Renewal Return Date',
                             help='The date when the custody is renewed and '
                                  'expected to be returned.')
    is_renew_return_date = fields.Boolean(string='Renewal Return Date',
                                          help='Indicates whether there is a '
                                               'renewal return date or not.')

    # State and return type
    state = fields.Selection(
        [('draft', 'Draft'), ('to_approve', 'Waiting For Approval'),
         ('approved', 'Approved'),
         ('returned', 'Returned'), ('rejected', 'Refused')], string='Status',
        help='The current status of the record')

    return_type = fields.Selection([
        ('date', 'Fixed Return Date'),
        ('flexible', 'No Fixed Return Date'),
        ('term_end', 'Return at Term/Project End')
    ], string='Return Type', help='Type of return arrangement')

    # Performance metrics computed fields
    return_performance = fields.Selection([
        ('early', 'Returned Early'),
        ('on_time', 'Returned On Time'),
        ('late', 'Returned Late'),
        ('not_returned', 'Not Yet Returned')
    ], string='Return Performance', help='Performance analysis of return timing')

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
                    t.actual_return_date as actual_return_date,
                    t.returned_by_id as returned_by_id,
                    t.is_overdue as is_overdue,
                    t.days_overdue as days_overdue,
                    t.return_type as return_type,
                    t.renew_date as renew_date,
                    t.is_renew_return_date as renew_return_date,
                    t.state as state,
                    CASE
                        WHEN t.state != 'returned' THEN 'not_returned'
                        WHEN t.return_type != 'date' THEN 'on_time'
                        WHEN t.actual_return_date < t.return_date THEN 'early'
                        WHEN t.actual_return_date = t.return_date THEN 'on_time'
                        WHEN t.actual_return_date > t.return_date THEN 'late'
                        ELSE 'on_time'
                    END as return_performance
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
                    actual_return_date,
                    returned_by_id,
                    is_overdue,
                    days_overdue,
                    return_type,
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
