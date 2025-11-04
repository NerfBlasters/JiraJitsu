import requests
import base64
import re
import json
import os
import logging
from . import config

logger = logging.getLogger(config.LOG_ALIAS)

"""
Wrapper class for all JitBit APIs
"""

class JitbitApi(object):

    def __init__(self, base_data=None, data_set_alias_dir=None, master_data_dir=None, debug=None):
        logger.info('Starting JitbitApi ..')

    def __del__(self):
        pass

    def check_url_and_user(self) -> bool:

        ret = False
        # Check URL and user authentication
        url = config.JITBIT_API_URL + '/Authorization'
        logger.info(f'Connecting to  URL: {url} ...')

        try:

            response = requests.get(url, auth=(config.JITBIT_USER, config.JITBIT_PWD))

            if response.status_code == 200:
                logger.info(f'Successfully connected to URL: {url}')
                logger.info(response.json())
                ret = True
            else:
                logger.critical(f'Error: Unable to completed: {url}')
                ret = False

        except Exception as e:
            logger.critical(str(e))
            raise

        return ret

    """
    Pass behalf_of if you want to create ticket for someone else. That is, "Created By" is different
    """

    def post_ticket(self, key: str, category_id: int, subject: str, body: str, priority_id: int, created_by: int, behalf_of: int | None = None) -> int:

        ret = -1

        url = config.JITBIT_API_URL + '/ticket'
        logger.info(f'[{key}] Connecting to  URL: {url} ...')
        in_data = {
                     'categoryId': category_id,
                     'subject': subject,
                     'body': body,
                     'priorityId': priority_id,
                     'userId': created_by
                  }

        logger.debug(in_data)

        try:
            response = requests.post(url, auth=(config.JITBIT_USER, config.JITBIT_PWD), data=in_data)

            if response.status_code == 200:
                logger.info(f'[{key}] Successfully connected to URL: {url}')
                ret = int(response.text)
            else:
                logger.critical(f'[{key}] ERROR: Unable to complete URL: {url}')
                ret = -1

        except Exception as e:
            logger.critical(str(e))
            raise

        return ret

    def post_comment(self, key: str, ticket_id: int, comment: str, comment_author_id: int) -> bool:

        assert ticket_id > 0
        ret = False

        url = config.JITBIT_API_URL + '/comment'
        logger.info(f'[{key}] Connecting to  URL: {url} ...')

        in_data = {'id': ticket_id, 'body': comment, 'fromUserId': comment_author_id}

        try:
            response = requests.post(url, auth=(config.JITBIT_USER, config.JITBIT_PWD), data=in_data)

            if response.status_code == 200:
                logger.info(f'[{key}] Successfully connected to URL: {url}')
                ret = True

            else:
                logger.critical(f'[{key}] ERROR: Unable to connect to URL: {url}')
                ret = False
                raise SystemError(ret)

        except Exception as e:
            logger.critical(str(e))
            raise

        return ret

    def post_attach_file(self, key: str, ticket_id: int, attach_file: str) -> bool:

        assert ticket_id > 0
        assert os.path.isfile(attach_file)
        ret = False
        url = config.JITBIT_API_URL + '/AttachFile'
        params = {'id': ticket_id}

        logger.info(f'[{key}] Connecting to  URL: {url} ...')

        in_data = {'file': open(attach_file, 'rb')}
        try:

            response = requests.post(url, auth=(config.JITBIT_USER, config.JITBIT_PWD), params=params, files=in_data)

            if response.status_code == 200:
                logger.info(f'[{key}] Successfully connected to URL: {url}')
                logger.info(response.text)
                ret = True
            else:
                logger.critical(f'[{key}] ERROR: Unable to connect to URL: {url}')
                ret = False
                raise SystemError(ret)

        except Exception as e:
            logger.critical(str(e))
            raise

        return ret

    def get_user_id_by_email(self, email: str) -> int:
        """
        Get JitBit user ID from email address.
        Returns user ID or default user ID if email is invalid or user not found.
        """
        # Validate email format
        if isinstance(email, int) or not email or not isinstance(email, str):
            logger.warning(f'{email} is not a valid email format, using default email')
            email = config.JITBIT_DEFAULT_ASSIGN_EMAIL

        url = config.JITBIT_API_URL + '/UserByEmail'
        params = {'email': email}
        logger.info(f'[{email}] Connecting to  URL: {url} ...')

        try:
            response = requests.get(url, auth=(config.JITBIT_USER, config.JITBIT_PWD), params=params)

            if response.status_code == 200:
                logger.info(f'[{email}] Successfully connected to URL: {url}')
                user_id = response.json()["UserID"]
                logger.info(f'User ID: {user_id}')
                return user_id

            else:
                logger.critical(f'[{email}] ERROR: Unable to connect to URL: {url}')
                # Return default user ID
                default_response = requests.get(
                    url,
                    auth=(config.JITBIT_USER, config.JITBIT_PWD),
                    params={'email': config.JITBIT_DEFAULT_ASSIGN_EMAIL}
                )
                if default_response.status_code == 200:
                    return default_response.json()["UserID"]
                return -1

        except Exception as e:
            logger.critical(str(e))
            raise


    def get_user_is_technician(self, user_id: int) -> bool:
        """
        Check if a user has the technician flag set in JitBit.
        Returns True if user is a technician, False otherwise.
        """
        url = config.JITBIT_API_URL + '/User'
        params = {'id': user_id}
        logger.info(f'[{user_id}] Checking technician status at URL: {url} ...')

        try:
            response = requests.get(url, auth=(config.JITBIT_USER, config.JITBIT_PWD), params=params)

            if response.status_code == 200:
                logger.info(f'[{user_id}] Successfully retrieved user info from URL: {url}')
                user_data = response.json()
                is_tech = user_data.get("IsTechie", False)
                logger.info(f'User {user_id} technician status: {is_tech}')
                return is_tech
            else:
                logger.warning(f'[{user_id}] ERROR: Unable to retrieve user info from URL: {url}')
                return False

        except Exception as e:
            logger.error(f'Error checking technician status for user {user_id}: {str(e)}')
            return False


    def post_set_ticket_status(self, key: str, ticket_id: int, status_id: int) -> bool:
        ret = False

        url = config.JITBIT_API_URL + '/UpdateTicket'
        logger.info(f'[{key}] Connecting to  URL: {url} ...')

        params = {'id': ticket_id, 'statusId': status_id}
        try:
            response = requests.post(url, auth=(config.JITBIT_USER, config.JITBIT_PWD), params=params)

            if response.status_code == 200:
                logger.info(f'[{key}] Successfully connected to URL: {url}')
                ret = True
            else:
                logger.critical(f'[{key}] ERROR: Unable to complete URL: {url}')
                ret = False
                raise SystemError(ret)

        except Exception as e:
            logger.critical(str(e))
            raise

        return ret

    def post_update_ticket(self, key: str, ticket_id: int, **kwargs) -> bool:
        """
        Universal method to update any ticket parameters.
        Accepts any valid UpdateTicket API parameters as kwargs:
        - assignedUserId: Assign to user
        - date: Created date
        - categoryId or newCategoryId: Category
        - priorityId: Priority
        - statusId: Status
        - dueDate: Due date
        - tags: Tags
        - subject: Subject
        - body: Body
        - timeSpentInSeconds: Time spent

        Example: post_update_ticket('KEY-1', 123, assignedUserId=5, date='2023-01-01')
        """
        ret = False
        url = config.JITBIT_API_URL + '/UpdateTicket'
        logger.info(f'[{key}] Connecting to  URL: {url} ...')

        # Ensure ticket ID is in the data
        in_data = {'id': ticket_id}

        # Handle both categoryId and newCategoryId (API accepts both)
        if 'categoryId' in kwargs:
            in_data['newCategoryId'] = kwargs.pop('categoryId')

        # Add all other parameters
        in_data.update(kwargs)

        logger.debug(f'Update data: {in_data}')

        try:
            response = requests.post(url, auth=(config.JITBIT_USER, config.JITBIT_PWD), data=in_data)

            if response.status_code == 200:
                logger.info(f'[{key}] Successfully updated ticket at URL: {url}')
                ret = True
            else:
                logger.critical(f'[{key}] ERROR: Unable to complete URL: {url}')
                raise SystemError(ret)

        except Exception as e:
            logger.critical(str(e))
            raise

        return ret

    # Keep legacy methods for backwards compatibility, but use post_update_ticket internally
    def post_set_assignee(self, key: str, ticket_id: int, assign_to_id: int, date_created: str) -> bool:
        """Legacy method - use post_update_ticket instead"""
        return self.post_update_ticket(key, ticket_id, assignedUserId=assign_to_id, date=date_created)

    def post_change_catetory(self, key: str, ticket_id: int, category_id: int) -> bool:
        """Legacy method - use post_update_ticket instead"""
        return self.post_update_ticket(key, ticket_id, categoryId=category_id)

    def post_mark_deleted(self, key: str, ticket_id: int) -> bool:

        assert ticket_id > 0

        # See if the tickets exists
        url = config.JITBIT_API_URL + '/ticket'
        logger.info(f'[{key}] Connecting to  URL: {url} ...')

        in_data = {'id': ticket_id}

        try:
            response = requests.get(url, auth=(config.JITBIT_USER, config.JITBIT_PWD), data=in_data)

            if response.status_code == 200:
                logger.info(f'[{key}] Successfully connected to URL: {url}')
                # Ticket exists. We move the category
                ret = self.post_change_catetory(key, ticket_id, config.JITBIT_DELETE_CATEGORY_ID)
            else:
                logger.critical(f'[{key}] ERROR: Unable to complete URL: {url}')
                ret = -1
                raise SystemError(ret)

        except Exception as e:
            logger.critical(str(e))
            raise

        return ret

    # Enhanced CLI methods

    def get_categories(self) -> list[dict]:
        """
        Get all JitBit categories
        Returns list of category dictionaries with CategoryID, Name, IsPrivate
        """
        url = config.JITBIT_API_URL + '/Categories'
        logger.info(f'Fetching categories from: {url}')

        try:
            response = requests.get(url, auth=(config.JITBIT_USER, config.JITBIT_PWD))

            if response.status_code == 200:
                categories = response.json()
                logger.info(f'Successfully fetched {len(categories)} categories')
                return categories
            else:
                logger.error(f'ERROR: Unable to fetch categories: {response.status_code}')
                return []

        except Exception as e:
            logger.critical(str(e))
            raise

    def get_users(self) -> list[dict]:
        """
        Get all JitBit users
        Returns list of user dictionaries
        """
        url = config.JITBIT_API_URL + '/Users'
        logger.info(f'Fetching users from: {url}')

        try:
            response = requests.get(url, auth=(config.JITBIT_USER, config.JITBIT_PWD))

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

    def create_user(self, email: str, first_name: str, last_name: str, is_technician: bool = False) -> int:
        """
        Create a new JitBit user
        Returns user ID if successful, -1 otherwise
        """
        url = config.JITBIT_API_URL + '/User'
        logger.info(f'Creating user: {email}')

        in_data = {
            'email': email,
            'firstName': first_name,
            'lastName': last_name,
            'isTechie': is_technician
        }

        try:
            response = requests.post(url, auth=(config.JITBIT_USER, config.JITBIT_PWD), data=in_data)

            if response.status_code == 200:
                user_id = int(response.text)
                logger.info(f'Successfully created user {email} with ID {user_id}')
                return user_id
            else:
                logger.error(f'ERROR: Unable to create user: {response.status_code}')
                return -1

        except Exception as e:
            logger.critical(str(e))
            raise

    def get_user_by_email_or_create(self, email: str, first_name: str = '', last_name: str = '',
                                     create_if_missing: bool = False, is_technician: bool = False) -> int:
        """
        Get user by email, optionally creating if not found
        Returns user ID or -1 if not found and not created
        """
        # Try to get existing user
        user_id = self.get_user_id_by_email(email)

        if user_id > 0:
            return user_id

        # User not found
        if create_if_missing:
            logger.info(f'User {email} not found, creating new user')
            # Parse name if not provided
            if not first_name and not last_name:
                name_parts = email.split('@')[0].split('.')
                first_name = name_parts[0] if len(name_parts) > 0 else 'Unknown'
                last_name = name_parts[1] if len(name_parts) > 1 else ''

            return self.create_user(email, first_name, last_name, is_technician)
        else:
            logger.warning(f'User {email} not found and create_if_missing is False')
            return -1

