

import requests
import base64
import re
import json
import os
import shutil
import logging
from . import config

logger = logging.getLogger(config.LOG_ALIAS)

"""
Wrapper class for all of JIRA APIs
"""

class JiraApi(object):

    def __init__(self, base_data=None, data_set_alias_dir=None, master_data_dir=None, debug=None):
        logger.info('Starting JiraApi ..')

    def __del__(self):
        pass

    """
    Used to test if user/pwd and URL are correct
    """

    def check_url_and_user(self) -> bool:

        ret = False
        # Check URL and user authentication
        url = config.JIRA_API_URL + '/issue/RFM-1'
        logger.info(f'Connecting to  URL: {url} ...')

        try:

            response = requests.get(url, auth=(config.JIRA_USER, config.JIRA_PWD))

            if response.status_code == 200:
                logger.info(f'Successfully connected to URL: {url}')
                ret = True
            else:
                logger.critical(f'Error: Unable to completed: {url}')
                ret = False

        except Exception as e:
            logger.critical(str(e))
            raise

        return ret

    def get_filter_for_id(self, filter_id: int) -> str:

        ret = ''
        # Check URL and user authentication
        url = config.JIRA_API_URL + '/filter/' + str(filter_id)

        logger.info(f'[{filter_id}] Connecting to  URL: {url} ...')

        try:

            response = requests.get(url, auth=(config.JIRA_USER, config.JIRA_PWD))

            if response.status_code == 200:
                logger.info(f'[{filter_id}] Successfully connected to URL: {url}')
                ret = response.json()['searchUrl']
            else:
                logger.critical(f'[{filter_id}] ERROR: Unable to completed: {url}')
                ret = ''

        except Exception as e:
            logger.critical(str(e))
            raise

        return ret

    def get_filter(self, url: str) -> dict:
        assert len(url) > 0, f'Not a valid url {url}'

        ret = ''

        # Limits the fields and rows returned.
        url += '&fields=key&maxResults=10000'

        logger.info(f'Connecting to  URL: {url} ...')

        try:

            response = requests.get(url, auth=(config.JIRA_USER, config.JIRA_PWD))

            if response.status_code == 200:
                logger.info(f'Successfully connected to URL: {url}')
                ret = response.json()
            else:
                logger.critical(f'ERROR: Unable to completed: {url}')
                ret = ''

        except Exception as e:
            logger.critical(str(e))
            raise

        return ret

    def get_issue_info(self, key: str) -> tuple[bool, dict | None]:

        # Check URL and user authentication
        url = config.JIRA_API_URL + '/issue/' + key
        logger.info(f'[{key}] Connecting to  URL: {url} ...')

        try:

            response = requests.get(url, auth=(config.JIRA_USER, config.JIRA_PWD))

            if response.status_code == 200:
                logger.info(f'[{key}] Successfully connected to URL: {url}')
                return True, response.json()
            else:
                logger.critical(f'[{key}] ERROR: Unable to completed: {url}')
                return False, None

        except Exception as e:
            logger.critical(str(e))
            raise

        return False, None

    def get_attachment(self, key: str, issue_info: dict) -> bool:

        ret = False

        # Iterate and get all the attachments
        attachments = issue_info['fields']['attachment']

        if len(attachments) == 0:
            logger.info(f'[{key}] No attachments found')
            return True

        key_dir = os.path.join(config.ATTACHMENT_FOLDER, key)

        if os.path.isdir(key_dir) and config.FETCH_ATTACHMENTS == config.NEW_ONLY:
            logger.info(f'[{key}] Attachments directory exists. Not fetching again as FETCH_ATTACHMENTS is set to: {config.FETCH_ATTACHMENTS}')
            return True

        key_dir = JiraApi.manage_folder(key)

        for attachment in attachments:
            file_name = attachment['filename']
            file_id = attachment['id']
            url = attachment['content']
            mime_type = attachment['mimeType']

            logger.info(f'[{key}] Connecting to  URL: {url} ...')

            try:
                response = requests.get(url, auth=(config.JIRA_USER, config.JIRA_PWD), stream=True)

                if response.status_code == 200:
                    logger.info(f'[{key}] Successfully connected to URL: {url}')
                    path = self._create_unique_name(key_dir, file_name)

                    with open(path, 'wb') as out_file:
                        shutil.copyfileobj(response.raw, out_file)

                    del response
                    ret = True
                else:
                    logger.critical(f'[{key}] ERROR: Unable to completed: {url}')
                    ret = False

            except Exception as e:
                logger.critical(str(e))
                raise

        return ret

    """
    Update the 'Tag' field in JIRA
    """

    def post_tag(self, key: str, tag: str) -> bool:

        url = config.JIRA_API_URL + '/issue/' + key
        logger.info(f'[{key}] Connecting to  URL: {url} ...')

        data_in = {'fields': {config.JIRA_TAG_FIELD: [tag]}}

        try:
            response = requests.put(url, auth=(config.JIRA_USER, config.JIRA_PWD), json=data_in)

            if response.status_code == 204:
                logger.info(f'[{key}] Successfully connected to URL: {url}')
                ret = True
            else:
                logger.critical(f'[{key}] ERROR: Unable to completed: {url}')
                ret = False
                raise SystemError(ret)

        except Exception as e:
            logger.critical(str(e))
            raise

        return ret


    @staticmethod
    def manage_folder(key: str) -> str:

        # key directories remove it it exists and recreate it
        key_dir = os.path.join(config.ATTACHMENT_FOLDER, key)
        if os.path.isdir(key_dir):
            shutil.rmtree(key_dir)
        os.mkdir(key_dir)

        return key_dir

    """
    Given a file name -- checks all the files in the directory
    and creates a unique file name if there is a conflict
    """
    def _create_unique_name(self, key_dir: str, file_name: str) -> str:

        path = os.path.join(key_dir, file_name)
        # If this name is unique nothing to do.
        if not os.path.isfile(path):
            return path

        # The file name already exists. We need to add a prefix to this file to make it unique
        uniq = 1
        while os.path.exists(path):
            uniq_name = str(uniq) + '_' + file_name
            path = os.path.join(key_dir, uniq_name)
            uniq += 1

        return path

    # Enhanced CLI methods

    def get_projects(self) -> list[dict]:
        """
        Get all JIRA projects
        Returns list of project dictionaries with key, name, and lead
        """
        url = config.JIRA_API_URL + '/project'
        logger.info(f'Fetching projects from: {url}')

        try:
            response = requests.get(url, auth=(config.JIRA_USER, config.JIRA_PWD))

            if response.status_code == 200:
                logger.info(f'Successfully fetched {len(response.json())} projects')
                return response.json()
            else:
                logger.error(f'ERROR: Unable to fetch projects: {response.status_code}')
                return []

        except Exception as e:
            logger.critical(str(e))
            raise

    def get_project_issue_count(self, project_key: str) -> int:
        """
        Count issues in a specific project
        """
        url = config.JIRA_API_URL + '/search'
        params = {
            'jql': f'project = {project_key}',
            'maxResults': 0  # We only want the total count
        }

        logger.info(f'Counting issues in project: {project_key}')

        try:
            response = requests.get(url, auth=(config.JIRA_USER, config.JIRA_PWD), params=params)

            if response.status_code == 200:
                count = response.json().get('total', 0)
                logger.info(f'Project {project_key} has {count} issues')
                return count
            else:
                logger.error(f'ERROR: Unable to count issues: {response.status_code}')
                return 0

        except Exception as e:
            logger.critical(str(e))
            raise

    def get_issue_types(self) -> list[dict]:
        """
        Get all JIRA issue types
        Returns list of issue type dictionaries
        """
        url = config.JIRA_API_URL + '/issuetype'
        logger.info(f'Fetching issue types from: {url}')

        try:
            response = requests.get(url, auth=(config.JIRA_USER, config.JIRA_PWD))

            if response.status_code == 200:
                logger.info(f'Successfully fetched {len(response.json())} issue types')
                return response.json()
            else:
                logger.error(f'ERROR: Unable to fetch issue types: {response.status_code}')
                return []

        except Exception as e:
            logger.critical(str(e))
            raise

    def get_issue_type_count(self, issue_type: str) -> int:
        """
        Count issues of a specific type across all projects
        """
        url = config.JIRA_API_URL + '/search'
        params = {
            'jql': f'issuetype = "{issue_type}"',
            'maxResults': 0
        }

        logger.info(f'Counting issues of type: {issue_type}')

        try:
            response = requests.get(url, auth=(config.JIRA_USER, config.JIRA_PWD), params=params)

            if response.status_code == 200:
                count = response.json().get('total', 0)
                logger.info(f'Issue type "{issue_type}" has {count} issues')
                return count
            else:
                logger.error(f'ERROR: Unable to count issue type: {response.status_code}')
                return 0

        except Exception as e:
            logger.critical(str(e))
            raise

    def get_filters(self) -> list[dict]:
        """
        Get all JIRA filters accessible to the current user
        Returns list of filter dictionaries
        """
        url = config.JIRA_API_URL + '/filter/favourite'
        logger.info(f'Fetching filters from: {url}')

        try:
            response = requests.get(url, auth=(config.JIRA_USER, config.JIRA_PWD))

            if response.status_code == 200:
                logger.info(f'Successfully fetched {len(response.json())} filters')
                return response.json()
            else:
                logger.error(f'ERROR: Unable to fetch filters: {response.status_code}')
                return []

        except Exception as e:
            logger.critical(str(e))
            raise

    def get_issues_by_jql(self, jql: str, max_results: int = 10000, fields: str = 'key') -> dict:
        """
        Generic JQL query method for flexible issue searching
        """
        url = config.JIRA_API_URL + '/search'
        params = {
            'jql': jql,
            'fields': fields,
            'maxResults': max_results
        }

        logger.info(f'Executing JQL query: {jql}')

        try:
            response = requests.get(url, auth=(config.JIRA_USER, config.JIRA_PWD), params=params)

            if response.status_code == 200:
                result = response.json()
                logger.info(f'JQL query returned {len(result.get("issues", []))} issues')
                return result
            else:
                logger.error(f'ERROR: JQL query failed: {response.status_code}')
                return {'issues': [], 'total': 0}

        except Exception as e:
            logger.critical(str(e))
            raise

    def get_issues_by_project(self, project: str, start_num: int | None = None,
                             end_num: int | None = None, max_results: int = 10000) -> dict:
        """
        Get issues from a specific project, optionally filtered by issue number range
        Example: project='RFM', start_num=100, end_num=200 returns RFM-100 through RFM-200
        """
        if start_num and end_num:
            jql = f'project = {project} AND issuekey >= {project}-{start_num} AND issuekey <= {project}-{end_num}'
        else:
            jql = f'project = {project}'

        return self.get_issues_by_jql(jql, max_results)

    def get_all_users(self) -> list[dict]:
        """
        Get all JIRA users
        Returns list of user dictionaries with name, emailAddress, displayName
        """
        url = config.JIRA_API_URL + '/user/search'
        params = {
            'username': '.',  # Search pattern that matches all users
            'maxResults': 10000
        }

        logger.info(f'Fetching all JIRA users from: {url}')

        try:
            response = requests.get(url, auth=(config.JIRA_USER, config.JIRA_PWD), params=params)

            if response.status_code == 200:
                users = response.json()
                logger.info(f'Successfully fetched {len(users)} users')
                return users
            else:
                logger.error(f'ERROR: Unable to fetch users: {response.status_code}')
                return []

        except Exception as e:
            logger.critical(str(e))
            raise

