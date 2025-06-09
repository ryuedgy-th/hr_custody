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

    def _check_column_exists(self, column_name):
        """Check if column exists in the table"""
        self._cr.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'hr_custody'
            AND column_name = %s
        """, (column_name,))
        return bool(self._cr.fetchone())

    def _select(self):
        """the function used to construct the
        SELECT statement for retrieving specific fields in a SQL query."""

        # Base fields that should always exist
        select_str = """
             SELECT
                    (select 1 ) AS nbr,
                    t.id as id,
                    t.name as name,
                    t.date_request as date_request,
                    t.employee_id as employee,
                    t.purpose as purpose,
                    t.custody_property_id as custody_name,
                    t.state as state
        """

        # Add approved_by_id if exists
        if self._check_column_exists('approved_by_id'):
            select_str += ",\n                    t.approved_by_id as approved_by_id"
        else:
            select_str += ",\n                    NULL as approved_by_id"

        # Add approved_date if exists
        if self._check_column_exists('approved_date'):
            select_str += ",\n                    t.approved_date as approved_date"
        else:
            select_str += ",\n                    NULL as approved_date"

        # Add return_date
        select_str += ",\n                    t.return_date as return_date"

        # Add actual_return_date if exists
        if self._check_column_exists('actual_return_date'):
            select_str += ",\n                    t.actual_return_date as actual_return_date"
        else:
            select_str += ",\n                    NULL as actual_return_date"

        # Add returned_by_id if exists
        if self._check_column_exists('returned_by_id'):
            select_str += ",\n                    t.returned_by_id as returned_by_id"
        else:
            select_str += ",\n                    NULL as returned_by_id"

        # Add is_overdue if exists
        if self._check_column_exists('is_overdue'):
            select_str += ",\n                    t.is_overdue as is_overdue"
        else:
            select_str += ",\n                    FALSE as is_overdue"

        # Add days_overdue if exists
        if self._check_column_exists('days_overdue'):
            select_str += ",\n                    t.days_overdue as days_overdue"
        else:
            select_str += ",\n                    0 as days_overdue"

        # Add return_type if exists
        if self._check_column_exists('return_type'):
            select_str += ",\n                    t.return_type as return_type"
        else:
            select_str += ",\n                    'date' as return_type"

        # Add renewal fields
        if self._check_column_exists('renew_date'):
            select_str += ",\n                    t.renew_date as renew_date"
        else:
            select_str += ",\n                    NULL as renew_date"

        if self._check_column_exists('is_renew_return_date'):
            select_str += ",\n                    t.is_renew_return_date as renew_return_date"
        else:
            select_str += ",\n                    FALSE as renew_return_date"

        # Add performance calculation
        select_str += """,
                    CASE
                        WHEN t.state != 'returned' THEN 'not_returned'
                        WHEN COALESCE(t.return_type, 'date') != 'date' THEN 'on_time'
                        WHEN t.actual_return_date IS NULL THEN 'not_returned'
                        WHEN t.return_date IS NULL THEN 'on_time'
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
                    state,
                    return_date
        """

        # Add conditional group by fields
        if self._check_column_exists('approved_by_id'):
            group_by_str += ",\n                    approved_by_id"
        if self._check_column_exists('approved_date'):
            group_by_str += ",\n                    approved_date"
        if self._check_column_exists('actual_return_date'):
            group_by_str += ",\n                    actual_return_date"
        if self._check_column_exists('returned_by_id'):
            group_by_str += ",\n                    returned_by_id"
        if self._check_column_exists('is_overdue'):
            group_by_str += ",\n                    is_overdue"
        if self._check_column_exists('days_overdue'):
            group_by_str += ",\n                    days_overdue"
        if self._check_column_exists('return_type'):
            group_by_str += ",\n                    return_type"
        if self._check_column_exists('renew_date'):
            group_by_str += ",\n                    renew_date"
        if self._check_column_exists('is_renew_return_date'):
            group_by_str += ",\n                    is_renew_return_date"

        return group_by_str

    def init(self):
        """The function used to initialize the
        database view 'report_custody' for reporting purposes."""
        tools.sql.drop_view_if_exists(self._cr, 'report_custody')

        try:
            self._cr.execute("""
                CREATE view report_custody as
                  %s
                  FROM hr_custody t
                    %s
            """ % (self._select(), self._group_by()))
            print("✅ Report view created successfully")
        except Exception as e:
            print(f"❌ Error creating report view: {e}")
            # Create a minimal view as fallback
            self._cr.execute("""
                CREATE view report_custody as
                SELECT
                    1 as nbr,
                    t.id as id,
                    t.name as name,
                    t.date_request as date_request,
                    t.employee_id as employee,
                    t.purpose as purpose,
                    t.custody_property_id as custody_name,
                    NULL as approved_by_id,
                    NULL as approved_date,
                    t.return_date as return_date,
                    NULL as actual_return_date,
                    NULL as returned_by_id,
                    FALSE as is_overdue,
                    0 as days_overdue,
                    'date' as return_type,
                    NULL as renew_date,
                    FALSE as renew_return_date,
                    t.state as state,
                    'not_returned' as return_performance
                FROM hr_custody t
                GROUP BY t.id, name, date_request, employee_id, purpose,
                         custody_property_id, return_date, state
            """)
            print("✅ Fallback report view created")
