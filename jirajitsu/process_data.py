
import os
import time
import logging
from datetime import datetime, timedelta
from . import config
import progressbar
from .argument_parser import ArgumentParser
from .log_handler import LogHandler
from .jitbit_api import JitbitApi
from .jira_api import JiraApi

logger = logging.getLogger(config.LOG_ALIAS)


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

    def __init__(self):
        logger.info('Starting ProcessData ..')
        self.jitbit_api = JitbitApi()
        self.jira_api = JiraApi()

        # All assigned by is set to one user.
        self.default_assign_id = self.jitbit_api.get_user_id_by_email(config.JITBIT_DEFAULT_ASSIGN_EMAIL)

        self.start_time = time.time()

    def __del__(self):
        end_time = time.time()
        exec_time = end_time - self.start_time
        logger.info(f'Total time to run: {exec_time} seconds.')

    def start(self):
        try:
            self.jira_api = JiraApi()

            # Check URL and user authentication
            if not self.jira_api.check_url_and_user():
                assert 'Check URL and User call failed!'

            # We want to run a specific filter in JIRA.
            # First give the filter Id and get the URL to run
            filter_url = self.jira_api.get_filter_for_id(config.JIRA_FILTER_ID)

            # Run the filter and get a list of issues to migrate
            issues_list = self.jira_api.get_filter(filter_url)

            # Setup progress bar
            total = len(issues_list['issues'])
            total_str = '/' + str(total)
            pbar_count = 0
            pbar = progressbar.ProgressBar(widgets=[progressbar.Bar(), progressbar.Counter(), total_str, ' ', progressbar.ETA(), ' ', progressbar.Timer()], maxval=total).start()

            # Iterate over each issue and get details
            for issue in issues_list['issues']:

                key = issue['key']

                pbar_count += 1
                pbar.update(pbar_count)
                logger.info(f'[{key}] Processing: {pbar_count}{total_str}')

                status, issue_info = self.jira_api.get_issue_info(key)

                if not status:
                    logger.critical(f'[{key}] ERROR: Not able to get issue info')
                    continue

                self.jira_api.get_attachment(key, issue_info)

                # Now create this issue in JitBit
                self._migrate_to_jitbit(key, issue_info)


            pbar.finish

        except Exception as e:
            logger.critical(str(e))
            raise


    def test_jitbit(self):

        # Use this to test a single post to JitBit.
        # Hardcoded key will be posted.

        process_key = 'RFM-1'
        try:
            self.jira_api = JiraApi()

            # Check URL and user authentication
            if not self.jira_api.check_url_and_user():
                assert 'Check URL and User call failed!'

            filter_url = self.jira_api.get_filter_for_id(config.JIRA_FILTER_ID)

            # Run the filter and get a list of issues to deal with
            issues_list = self.jira_api.get_filter(filter_url)

            # Iterate over each issue and get details
            for issue in issues_list['issues']:

                key = issue['key']

                if key != process_key:
                    continue

                status, issue_info = self.jira_api.get_issue_info(key)

                if not status:
                    logger.critical(f'[{key}] ERROR: Not able to get issue info')
                    continue

                self.jira_api.get_attachment(key, issue_info)

                # Now create this issue in JitBit
                self._migrate_to_jitbit(key, issue_info)

        except Exception as e:
            logger.critical(str(e))
            raise

    def _migrate_to_jitbit(self, key: str, issue_info: dict):

        ticket_id = -1

        try:
            category_id = config.JITBIT_MIGRATE_CATEGORY_ID

            # We append JIRA key to subject
            subject = issue_info['fields']['summary'] + ' (' + key + ')'

            body = issue_info['fields']['description'] + '\n\n' + '(Originally assigned to: ' + issue_info['fields']['assignee']['displayName'] +  ')\n' + '(Original Resolution date: ' + issue_info['fields']['resolutiondate'][:10] + ')\n'
            if body is None:
                body = ''

            # We will set all of the priorities to Normal (0)
            priority_id = 0

            # Status. JitBit has only New(1) and Closed(3) exposed via API
            ## our statusname is Done - changed from 'closed'
            if (issue_info['fields']['status']['name']).lower() == 'done':
                status_id = 3
            else:
                status_id = 1

            # Created by
            # By default this will be the person creating the ticket.
            # You can create 'on-behalf' of another person
            # This code will get the details of the user from JIRA

            created_by_email = issue_info['fields']['creator']['emailAddress']
            logger.debug(f'Variable created_by_email is [{created_by_email}]')
            created_by = self.jitbit_api.get_user_id_by_email(created_by_email)
            logger.debug(f'Variable created_by is [{created_by}]')

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

                # Check if user has technician flag
                if assign_to_id > 0:
                    is_technician = self.jitbit_api.get_user_is_technician(assign_to_id)
                    if not is_technician:
                        logger.warning(f'User {assign_to_id} ({assign_to_email}) is not a technician, using default assignee')
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

            # Ready to create the ticket
            ticket_id = int(self.jitbit_api.post_ticket(key, category_id, subject, body, priority_id, created_by,
                                                        behalf_of=assign_to_id,
                                                        custom_fields=custom_fields if custom_fields else None))
            if ticket_id > 0:

                # Update ticket with date and assignee
                update_params = {
                    'assignedUserId': assign_to_id,
                    'date': date_created
                }

                self.jitbit_api.post_update_ticket(key, ticket_id, **update_params)

                self._add_comments(key, ticket_id, issue_info)
                self._add_attachments(key, ticket_id, issue_info)

                # Set status first
                self.jitbit_api.post_set_ticket_status(key, ticket_id, status_id)

                # Then set closeDate AFTER status is set (for closed tickets only)
                # JitBit may require the ticket to already be closed before accepting a historical closeDate
                if close_date:
                    logger.debug(f'Setting closeDate after status change: {close_date}')
                    self.jitbit_api.post_update_ticket(key, ticket_id, closeDate=close_date)

                # We update the issue on the JIRA side if the migration was successful.
                # We use the 'Tag' field in JIRA for this
                # Uncomment if you want to tag migrated issues in JIRA
                # self.jira_api.post_tag(key, config.JITBIT_MIGRATION_SUCCESS)
            else:
                logger.critical(f'ERROR: could not create a ticket in JitBit for {key}')

        except Exception as e:

            # If we have a failure anywhere in the process we have to delete the ticket.
            # However, JitBit API does not support delete of tickets.
            # Instead move the ticket to 'Deleted' category.
            if ticket_id > 0:
                self.jitbit_api.post_mark_deleted(key, ticket_id)
                logger.critical(f'{str(e)} - Marked ticket {ticket_id} for deletion')
            else:
                logger.critical(str(e))
            # Don't raise let continue

    def _add_comments(self, key: str, ticket_id: int, issue_info: dict):
        assert ticket_id > 0

        comments = issue_info['fields']['comment']
        for comment in comments['comments']:
            comment_text = comment['body']
            # Comments can be anonymous - use default user ID
            comment_author_id = self.default_assign_id
            comment_timestamp = comment['updated'][:10]
            if 'updateAuthor' in comment:
                comment_author = comment['updateAuthor'].get('emailAddress')
                if comment_author:
                    comment_author_id = self.jitbit_api.get_user_id_by_email(comment_author)
                    # If user lookup fails, fall back to default
                    if comment_author_id <= 0:
                        comment_author_id = self.default_assign_id
                        logger.debug(f'Comment author lookup failed for {comment_author}, using default user')


            comment_data = '(Originally posted on: ' + comment_timestamp + ')\n\n' + comment_text
            self.jitbit_api.post_comment(key, ticket_id, comment_data, comment_author_id)

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
                else:
                    logger.info(f'[{key}] File size is < 5K. Ignoring. {file_dir}')


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

