
import os
import time
import logging
from datetime import datetime, timedelta
from . import config
import progressbar
from rich.console import Console
from rich.table import Table
from .argument_parser import ArgumentParser
from .log_handler import LogHandler
from .jitbit_api import JitbitApi
from .jira_api import JiraApi

logger = logging.getLogger(config.LOG_ALIAS)
console = Console()


def convert_utc_to_central(utc_timestamp: str) -> str:
    """
    Convert UTC timestamp to Central Time (UTC-5).

    Args:
        utc_timestamp: ISO 8601 timestamp string (e.g., '2024-01-01T10:00:00.000+0000')

    Returns:
        Central Time timestamp in same format
    """
    try:
        # Parse the UTC timestamp (handle both with and without milliseconds)
        if '.' in utc_timestamp:
            # Has milliseconds: 2024-01-01T10:00:00.000+0000
            dt = datetime.strptime(utc_timestamp[:23], '%Y-%m-%dT%H:%M:%S.%f')
        else:
            # No milliseconds: 2024-01-01T10:00:00+0000
            dt = datetime.strptime(utc_timestamp[:19], '%Y-%m-%dT%H:%M:%S')

        # Subtract 5 hours for Central Time
        central_dt = dt - timedelta(hours=5)

        # Format back to ISO 8601 (maintain original format)
        if '.' in utc_timestamp:
            return central_dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '-0500'
        else:
            return central_dt.strftime('%Y-%m-%dT%H:%M:%S') + '-0500'
    except Exception as e:
        logger.error(f'Error converting timestamp {utc_timestamp}: {str(e)}')
        return utc_timestamp  # Return original on error


def calculate_start_date(issue_info: dict) -> str | None:
    """
    Calculate the start date for a ticket based on:
    1. First comment timestamp (if exists)
    2. First assignee change from changelog (if exists)
    3. Resolution date as fallback

    Args:
        issue_info: Jira issue information dictionary

    Returns:
        Central Time timestamp string or None if cannot be determined
    """
    try:
        # Priority 1: First comment timestamp
        comments = issue_info.get('fields', {}).get('comment', {}).get('comments', [])
        if comments:
            first_comment_time = comments[0].get('created') or comments[0].get('updated')
            if first_comment_time:
                logger.debug(f'Start date from first comment: {first_comment_time}')
                return convert_utc_to_central(first_comment_time)

        # Priority 2: First assignee change from changelog
        changelog = issue_info.get('changelog', {}).get('histories', [])
        for history in changelog:
            items = history.get('items', [])
            for item in items:
                if item.get('field') == 'assignee':
                    assignee_timestamp = history.get('created')
                    if assignee_timestamp:
                        logger.debug(f'Start date from assignee change: {assignee_timestamp}')
                        return convert_utc_to_central(assignee_timestamp)

        # Priority 3: Resolution date as fallback
        resolution_date = issue_info.get('fields', {}).get('resolutiondate')
        if resolution_date:
            logger.debug(f'Start date from resolution date: {resolution_date}')
            return convert_utc_to_central(resolution_date)

        logger.warning('Unable to calculate start date, no comments or assignee history found')
        return None

    except Exception as e:
        logger.error(f'Error calculating start date: {str(e)}')
        return None


def calculate_close_date(issue_info: dict, assignee_email: str | None) -> str | None:
    """
    Calculate the close date for a ticket based on:
    1. Last comment from current assignee (if exists)
    2. Resolution date as fallback

    Only calculates for closed/resolved tickets.

    Args:
        issue_info: Jira issue information dictionary
        assignee_email: Email of the current assignee

    Returns:
        Central Time timestamp string or None if ticket is open or cannot be determined
    """
    try:
        # Only calculate closeDate for closed/resolved tickets
        status = issue_info.get('fields', {}).get('status', {}).get('name', '').lower()
        if status not in ['done', 'closed', 'resolved']:
            logger.debug(f'Ticket status is "{status}", not setting close date (ticket is open)')
            return None

        # Priority 1: Last comment from current assignee
        if assignee_email:
            comments = issue_info.get('fields', {}).get('comment', {}).get('comments', [])
            # Search backwards through comments to find last comment from assignee
            for comment in reversed(comments):
                author_email = comment.get('updateAuthor', {}).get('emailAddress')
                if author_email == assignee_email:
                    comment_time = comment.get('updated') or comment.get('created')
                    if comment_time:
                        logger.debug(f'Close date from assignee comment: {comment_time}')
                        return convert_utc_to_central(comment_time)

        # Priority 2: Resolution date as fallback
        resolution_date = issue_info.get('fields', {}).get('resolutiondate')
        if resolution_date:
            logger.debug(f'Close date from resolution date: {resolution_date}')
            return convert_utc_to_central(resolution_date)

        logger.warning('Ticket is closed but unable to calculate close date')
        return None

    except Exception as e:
        logger.error(f'Error calculating close date: {str(e)}')
        return None


class ProcessData(object):

    def __init__(self, create_missing_users: bool = False):
        logger.info('Starting ProcessData ..')
        self.jitbit_api = JitbitApi()
        self.jira_api = JiraApi()

        # All assigned by is set to one user.
        self.default_assign_id = self.jitbit_api.get_user_id_by_email(config.JITBIT_DEFAULT_ASSIGN_EMAIL)

        # User creation settings
        self.create_missing_users = create_missing_users
        self.created_users = []  # Track created users: [(email, first_name, last_name, user_id), ...]

        # Migration statistics
        self.stats = {
            'total_tickets': 0,
            'tickets_created': 0,
            'tickets_updated': 0,
            'comments_added': 0,
            'comments_skipped': 0,
            'attachments_added': 0,
            'failed_tickets': 0,
            'cached_technicians': 0
        }

        self.start_time = time.time()

    def __del__(self):
        end_time = time.time()
        exec_time = end_time - self.start_time
        logger.info(f'Total time to run: {exec_time} seconds.')

        # Log created users to file
        if self.created_users:
            import csv
            from datetime import datetime
            log_file = os.path.join(config.LOG_DIR, f'created_users_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
            try:
                with open(log_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Email', 'First Name', 'Last Name', 'JitBit User ID'])
                    writer.writerows(self.created_users)
                logger.info(f'Created {len(self.created_users)} users - logged to {log_file}')
            except Exception as e:
                logger.error(f'Failed to write created users log: {str(e)}')

    def start(self, issues_list=None):
        try:
            self.jira_api = JiraApi()

            # Check URL and user authentication
            if not self.jira_api.check_url_and_user():
                assert 'Check URL and User call failed!'

            # If no issues list provided, use default filter from config
            if issues_list is None:
                # We want to run a specific filter in JIRA.
                # First give the filter Id and get the URL to run
                filter_url = self.jira_api.get_filter_for_id(config.JIRA_FILTER_ID)

                # Run the filter and get a list of issues to migrate
                issues_list = self.jira_api.get_filter(filter_url)

            # Pre-load user caches to minimize API calls during migration
            tech_count = self.jitbit_api.preload_user_caches(config.JITBIT_MIGRATE_CATEGORY_ID)
            self.stats['cached_technicians'] = tech_count

            # Setup progress bar
            total = len(issues_list['issues'])
            total_str = '/' + str(total)
            pbar_count = 0
            pbar = progressbar.ProgressBar(widgets=[progressbar.Bar(), progressbar.Counter(), total_str, ' ', progressbar.ETA(), ' ', progressbar.Timer()], maxval=total).start()

            # Iterate over each issue and get details
            for issue in issues_list['issues']:

                key = issue['key']

                self.stats['total_tickets'] += 1
                pbar_count += 1
                pbar.update(pbar_count)
                logger.info(f'[{key}] Processing: {pbar_count}{total_str}')

                status, issue_info = self.jira_api.get_issue_info(key)

                if not status:
                    logger.critical(f'[{key}] ERROR: Not able to get issue info')
                    self.stats['failed_tickets'] += 1
                    continue

                self.jira_api.get_attachment(key, issue_info)

                # Log key ticket metadata
                reporter = issue_info['fields'].get('reporter') or issue_info['fields'].get('creator', {})
                reporter_email = reporter.get('emailAddress', 'Unknown') if reporter else 'Unknown'
                logger.info(f'[{key}] Reporter: {reporter_email}')

                assignee = issue_info['fields'].get('assignee')
                assignee_email = assignee.get('emailAddress', 'Unassigned') if assignee else 'Unassigned'
                logger.info(f'[{key}] Assignee: {assignee_email}')

                watchers = issue_info['fields'].get('watches', {})
                watcher_count = watchers.get('watchCount', 0)
                logger.info(f'[{key}] Watchers: {watcher_count}')

                comments = issue_info['fields'].get('comment', {})
                comment_count = len(comments.get('comments', []))
                logger.info(f'[{key}] JIRA Comments: {comment_count}')

                # Now create this issue in JitBit
                self._migrate_to_jitbit(key, issue_info)


            pbar.finish()

            # Display migration summary
            end_time = time.time()
            execution_time = end_time - self.start_time
            self.display_summary(execution_time)

        except Exception as e:
            logger.critical(str(e))
            raise


    def test_jitbit(self):

        # Use this to test a single post to JitBit.
        # Uses the first issue from the configured filter.

        try:
            self.jira_api = JiraApi()

            # Check URL and user authentication
            if not self.jira_api.check_url_and_user():
                assert 'Check URL and User call failed!'

            filter_url = self.jira_api.get_filter_for_id(config.JIRA_FILTER_ID)

            # Run the filter and get a list of issues to deal with
            issues_list = self.jira_api.get_filter(filter_url)

            if not issues_list['issues']:
                logger.critical('No issues found in filter')
                return

            # Use the first issue from the filter
            issue = issues_list['issues'][0]
            key = issue['key']
            logger.info(f'Testing with issue: {key}')

            # Process this single issue
            status, issue_info = self.jira_api.get_issue_info(key)

            if not status:
                logger.critical(f'[{key}] ERROR: Not able to get issue info')
                return

            self.jira_api.get_attachment(key, issue_info)

            # Log key ticket metadata
            reporter = issue_info['fields'].get('reporter') or issue_info['fields'].get('creator', {})
            reporter_email = reporter.get('emailAddress', 'Unknown') if reporter else 'Unknown'
            logger.info(f'[{key}] Reporter: {reporter_email}')

            assignee = issue_info['fields'].get('assignee')
            assignee_email = assignee.get('emailAddress', 'Unassigned') if assignee else 'Unassigned'
            logger.info(f'[{key}] Assignee: {assignee_email}')

            watchers = issue_info['fields'].get('watches', {})
            watcher_count = watchers.get('watchCount', 0)
            logger.info(f'[{key}] Watchers: {watcher_count}')

            comments = issue_info['fields'].get('comment', {})
            comment_count = len(comments.get('comments', []))
            logger.info(f'[{key}] JIRA Comments: {comment_count}')

            # Now create this issue in JitBit
            self._migrate_to_jitbit(key, issue_info)

        except Exception as e:
            logger.critical(str(e))
            raise

    def _create_user_from_jira_info(self, jira_user_info: dict) -> int:
        """
        Create a JitBit user from JIRA user info
        Returns user ID if successful, -1 otherwise
        """
        email = jira_user_info.get('emailAddress', '')
        display_name = jira_user_info.get('displayName', '')

        if not email:
            logger.warning('Cannot create user without email address')
            return -1

        # Parse name from displayName
        name_parts = display_name.split()
        first_name = name_parts[0] if len(name_parts) > 0 else display_name
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

        # Create user
        logger.info(f'Creating missing user: {first_name} {last_name} ({email})')
        user_id = self.jitbit_api.create_user(email, first_name, last_name)

        if user_id > 0:
            # Track created user
            self.created_users.append((email, first_name, last_name, user_id))
            logger.info(f'Successfully created user {email} with ID {user_id}')
        else:
            logger.error(f'Failed to create user {email}')

        return user_id

    def _migrate_to_jitbit(self, key: str, issue_info: dict):

        ticket_id = -1

        try:
            category_id = config.JITBIT_MIGRATE_CATEGORY_ID

            # We append JIRA key to subject
            subject = issue_info['fields']['summary'] + ' (' + key + ')'

            # Build body with null-safe concatenation
            description = issue_info['fields'].get('description') or ''

            # Add assignee info if available
            assignee_name = ''
            if issue_info['fields'].get('assignee'):
                assignee_name = issue_info['fields']['assignee'].get('displayName', '')

            # Add resolution date if available
            resolution_date = ''
            if issue_info['fields'].get('resolutiondate'):
                resolution_date = issue_info['fields']['resolutiondate'][:10]

            # Build body with metadata only if available
            body = description
            if assignee_name:
                body += f'\n\n(Originally assigned to: {assignee_name})'
            if resolution_date:
                body += f'\n(Original Resolution date: {resolution_date})'
            if not body:
                body = ''

            # We will set all of the priorities to Normal (0)
            priority_id = 0

            # Status. JitBit has only New(1) and Closed(3) exposed via API
            ## Map various JIRA closed statuses to JitBit closed (3)
            jira_status = (issue_info['fields']['status']['name']).lower()
            logger.info(f'[{key}] JIRA status: {jira_status}')

            # Statuses that indicate ticket is closed/resolved
            closed_statuses = ['done', 'closed', 'resolved', 'complete', 'completed', 'fixed', 'canceled', 'cancelled']

            if jira_status in closed_statuses:
                status_id = 3  # Closed in JitBit
                logger.info(f'[{key}] Mapping to JitBit Closed (3)')
            else:
                status_id = 1  # New/Open in JitBit
                logger.info(f'[{key}] Mapping to JitBit New (1)')

            # Created by / Reporter
            # Use reporter field (not creator) - reporter is who reported the issue
            # Creator is who created it in Jira (often admins migrating from other systems)
            # Fallback to creator if reporter doesn't exist

            reporter_field = issue_info['fields'].get('reporter') or issue_info['fields'].get('creator')
            if reporter_field:
                created_by_email = reporter_field.get('emailAddress')
            else:
                created_by_email = None

            logger.debug(f'Variable created_by_email is [{created_by_email}]')
            created_by = self.jitbit_api.get_user_id_by_email(created_by_email)
            logger.debug(f'Variable created_by is [{created_by}]')

            # Auto-create user if missing and flag is set
            if created_by <= 0 and self.create_missing_users:
                logger.info(f'[{key}] Reporter {created_by_email} not found, attempting to create')
                created_by = self._create_user_from_jira_info(reporter_field)
                if created_by <= 0:
                    # Fall back to default if creation failed
                    logger.warning(f'[{key}] Failed to create creator, using default user')
                    created_by = self.default_assign_id
            elif created_by <= 0:
                # No auto-create, use default
                logger.warning(f'[{key}] Reporter {created_by_email} not found, using default user')
                created_by = self.default_assign_id

            # Get original Jira assignee info (before any JitBit mapping)
            # Used for: close date calculation AND populating the "Jira Assignee" custom field
            jira_assignee_email = None
            jira_assignee_name = None
            if issue_info['fields']['assignee']:
                jira_assignee_email = issue_info['fields']['assignee'].get('emailAddress')
                jira_assignee_name = issue_info['fields']['assignee'].get('displayName')

            # Assigned to - determine JitBit assignee
            # Check if assignee exists and get their user ID
            if issue_info['fields']['assignee'] is None or issue_info['fields']['assignee'].get('emailAddress') is None:
                assign_to_id = self.default_assign_id
                logger.debug(f'[{assign_to_id}] No assignee found, using default')
            else:
                assign_to_email = issue_info['fields']['assignee']['emailAddress']
                logger.debug(f'Variable assign_to_email is {assign_to_email}')

                # Get user ID from email
                assign_to_id = self.jitbit_api.get_user_id_by_email(assign_to_email)
                logger.debug(f'Variable assign_to_id is [{assign_to_id}]')

                # Auto-create user if missing and flag is set
                if assign_to_id <= 0 and self.create_missing_users:
                    logger.info(f'[{key}] Assignee {assign_to_email} not found, attempting to create')
                    assign_to_id = self._create_user_from_jira_info(issue_info['fields']['assignee'])

                # Check if user has technician flag
                if assign_to_id > 0:
                    is_technician = self.jitbit_api.get_user_is_technician(assign_to_id)
                    if not is_technician:
                        logger.warning(f'User {assign_to_id} ({assign_to_email}) is not a technician, attempting to grant permissions')
                        # Try to grant technician permission for this category
                        if self.jitbit_api.add_category_tech_permission(assign_to_id, category_id):
                            logger.info(f'Successfully granted technician permission to user {assign_to_id} for category {category_id}')
                            # User is now a technician, can keep as assignee
                        else:
                            logger.warning(f'Failed to grant technician permission, using default assignee')
                            assign_to_id = self.default_assign_id
                else:
                    logger.warning(f'Invalid user ID for {assign_to_email}, using default assignee')
                    assign_to_id = self.default_assign_id

            # Created timestamp - convert to Central Time
            # Goes in /updateticket as 'date'
            date_created = convert_utc_to_central(issue_info['fields']['created'])
            logger.debug(f'Created date (Central Time): {date_created}')

            # Calculate startDate and closeDate based on ORIGINAL Jira data
            start_date = calculate_start_date(issue_info)
            close_date = calculate_close_date(issue_info, jira_assignee_email)

            # Prepare custom fields - populate "Jira Assignee" field with original Jira assignee name
            custom_fields = {}
            if jira_assignee_name:
                custom_fields[config.JITBIT_JIRA_ASSIGNEE_FIELD_ID] = jira_assignee_name
                logger.debug(f'[{key}] Will set Jira Assignee custom field to: {jira_assignee_name}')

            # Check for duplicate ticket - search by Jira key
            existing_ticket_id = self.jitbit_api.search_tickets_by_jira_key(key)

            if existing_ticket_id:
                # Ticket already exists - update instead of creating new
                logger.info(f'[{key}] Ticket already exists (ID: {existing_ticket_id}), will update instead of creating new')
                ticket_id = existing_ticket_id
                self.stats['tickets_updated'] += 1
            else:
                # No duplicate found - create new ticket
                logger.info(f'[{key}] No existing ticket found, creating new ticket')
                ticket_id = int(self.jitbit_api.post_ticket(key, category_id, subject, body, priority_id, created_by,
                                                            behalf_of=assign_to_id,
                                                            custom_fields=custom_fields if custom_fields else None))
                self.stats['tickets_created'] += 1

            if ticket_id > 0:

                # Add comments and attachments first (while ticket is in initial status)
                # This prevents comments from reopening a closed ticket
                self._add_comments(key, ticket_id, issue_info)
                self._add_attachments(key, ticket_id, issue_info)

                # Update ticket last with consolidated API call
                # Set all fields in one call to minimize API usage
                # NOTE: userId is set during ticket creation (post_ticket), not in updates
                update_params = {
                    'assignedUserId': assign_to_id,
                    'date': date_created,
                    'statusId': status_id
                }

                update_success = self.jitbit_api.post_update_ticket(key, ticket_id, **update_params)

                # JitBit overrides closeDate when closing a ticket, so update it after status change succeeds
                if update_success and close_date and status_id == 3:
                    self.jitbit_api.post_update_close_date(key, ticket_id, close_date)

                # We update the issue on the JIRA side if the migration was successful.
                # We use the 'Tag' field in JIRA for this
                # Uncomment if you want to tag migrated issues in JIRA
                # self.jira_api.post_tag(key, config.JITBIT_MIGRATION_SUCCESS)
            else:
                logger.critical(f'ERROR: could not create a ticket in JitBit for {key}')
                self.stats['failed_tickets'] += 1

        except Exception as e:

            # If we have a failure anywhere in the process we have to delete the ticket.
            # However, JitBit API does not support delete of tickets.
            # Instead move the ticket to 'Deleted' category.
            if ticket_id > 0:
                self.jitbit_api.post_mark_deleted(key, ticket_id)
                logger.critical(f'{str(e)} - Marked ticket {ticket_id} for deletion')
            else:
                logger.critical(str(e))
            self.stats['failed_tickets'] += 1
            # Don't raise let continue

    def _add_comments(self, key: str, ticket_id: int, issue_info: dict):
        assert ticket_id > 0

        # Fetch existing comments to avoid duplicates
        existing_comments = self.jitbit_api.get_ticket_comments(key, ticket_id)

        # Build a set of timestamps that already exist in JitBit comments
        # Extract timestamp from "(Originally posted on: YYYY-MM-DD HH:MM:SS)" prefix
        # JitBit may return different formats:
        #   - "<!--html-->(Originally posted on: YYYY-MM-DD HH:MM:SS)<br><br>..." (HTML breaks)
        #   - "<!--html-->(Originally posted on: YYYY-MM-DD HH:MM:SS)\n\n..." (literal newlines)
        existing_timestamps = set()
        for existing_comment in existing_comments:
            body = existing_comment.get('Body', '')
            # Strip HTML comment prefix if present
            if body.startswith('<!--html-->'):
                body = body[11:]  # Remove "<!--html-->"

            # Check for format: "(Originally posted on: ...)"
            if body.startswith('(Originally posted on: '):
                # Look for closing paren followed by either HTML break or newline
                # Try <br> first (HTML format)
                end_idx = body.find(')<br>')
                if end_idx == -1:
                    # Try \n format (literal newline)
                    end_idx = body.find(')\n')

                if end_idx > 23:
                    timestamp = body[23:end_idx]  # Extract the timestamp
                    existing_timestamps.add(timestamp)
                    logger.debug(f'[{key}] Extracted existing timestamp: "{timestamp}"')

        # Log JitBit comment status
        logger.info(f'[{key}] Found {len(existing_comments)} existing JitBit comments ({len(existing_timestamps)} previously migrated from JIRA)')
        if existing_timestamps:
            logger.debug(f'[{key}] Existing migrated timestamps: {existing_timestamps}')

        # Log JIRA comment count
        comments = issue_info['fields']['comment']
        jira_comment_count = len(comments['comments'])
        logger.info(f'[{key}] Migrating {jira_comment_count} JIRA comments to JitBit')

        comments_added = 0
        comments_skipped = 0

        for comment in comments['comments']:
            comment_text = comment['body']
            # Comments can be anonymous - use default user ID
            comment_author_id = self.default_assign_id
            # Use raw timestamp from Jira (already in correct timezone)
            # Jira format: "2024-01-15T14:30:45.123+0000"
            comment_timestamp_full = comment['updated']
            # Extract readable format: YYYY-MM-DD HH:MM:SS
            comment_timestamp = comment_timestamp_full[:10] + ' ' + comment_timestamp_full[11:19]
            if 'updateAuthor' in comment:
                comment_author = comment['updateAuthor'].get('emailAddress')
                if comment_author:
                    comment_author_id = self.jitbit_api.get_user_id_by_email(comment_author)
                    # Auto-create user if missing and flag is set
                    if comment_author_id <= 0 and self.create_missing_users:
                        logger.info(f'[{key}] Comment author {comment_author} not found, attempting to create')
                        comment_author_id = self._create_user_from_jira_info(comment['updateAuthor'])
                    # If user lookup or creation failed, fall back to default
                    if comment_author_id <= 0:
                        comment_author_id = self.default_assign_id
                        logger.debug(f'Comment author lookup failed for {comment_author}, using default user')


            comment_data = '(Originally posted on: ' + comment_timestamp + ')\n\n' + comment_text

            # Check if a comment with this timestamp already exists in JitBit
            logger.debug(f'[{key}] Checking new comment timestamp: "{comment_timestamp}"')
            if comment_timestamp in existing_timestamps:
                logger.info(f'[{key}] Comment from {comment_timestamp} already exists, skipping')
                comments_skipped += 1
            else:
                logger.debug(f'[{key}] Timestamp not found in existing set, posting comment')
                self.jitbit_api.post_comment(key, ticket_id, comment_data, comment_author_id)
                comments_added += 1

        # Accumulate to migration statistics
        self.stats['comments_added'] += comments_added
        self.stats['comments_skipped'] += comments_skipped

        if comments_skipped > 0:
            logger.info(f'[{key}] Added {comments_added} new comments, skipped {comments_skipped} duplicates')

    def _add_attachments(self, key: str, ticket_id: int, issue_info: dict):

        # We will add all the files under the <attachments>/key directory to this issue
        key_dir = os.path.join(config.ATTACHMENT_FOLDER, key)

        if not os.path.exists(key_dir):
            logger.info(f'[{key}] No attachments to process')
            return

        for root, sub_dirs, files in os.walk(key_dir, topdown=True):
            for filename in files:
                file_dir = os.path.join(root, filename)
                # Ignore attachments of size 5K or less. These are normally logos or icons that we can skip
                if os.path.getsize(file_dir) > 5120:
                    self.jitbit_api.post_attach_file(key, ticket_id, file_dir)
                    self.stats['attachments_added'] += 1
                else:
                    logger.info(f'[{key}] File size is < 5K. Ignoring. {file_dir}')

    def display_summary(self, execution_time: float):
        """
        Display a summary table of migration statistics.
        """
        table = Table(title="Migration Summary", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Count", justify="right", style="green")

        # Format execution time
        minutes = int(execution_time // 60)
        seconds = int(execution_time % 60)
        if minutes > 0:
            time_str = f"{minutes}m {seconds}s"
        else:
            time_str = f"{seconds}s"

        # Add rows
        table.add_row("Total Tickets Processed", str(self.stats['total_tickets']))
        table.add_row("Tickets Created", str(self.stats['tickets_created']))
        table.add_row("Tickets Updated (existing)", str(self.stats['tickets_updated']))
        table.add_row("Comments Added", str(self.stats['comments_added']))
        table.add_row("Comments Skipped (duplicate)", str(self.stats['comments_skipped']))
        table.add_row("Attachments Added", str(self.stats['attachments_added']))
        table.add_row("Users Created", str(len(self.created_users)))
        table.add_row("Technicians (cached)", str(self.stats['cached_technicians']))
        table.add_row("Failed Tickets", str(self.stats['failed_tickets']), style="red" if self.stats['failed_tickets'] > 0 else "green")
        table.add_row("Execution Time", time_str, style="yellow")

        console.print("\n")
        console.print(table)
        console.print("\n")


def main():

    level = ArgumentParser().start()

    if level is not None:
        LogHandler(log_level=level)
    else:
        LogHandler()

    process_data = ProcessData()

    #process_data.test_jitbit()
    process_data.start()

if __name__ == '__main__':
    main()

