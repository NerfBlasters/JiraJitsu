import requests
import base64
import re
import json
import os
import logging
import time
from collections import deque
from . import config

logger = logging.getLogger(config.LOG_ALIAS)

"""
Wrapper class for all JitBit APIs
"""

class JitbitApi(object):

    def __init__(self, base_data=None, data_set_alias_dir=None, master_data_dir=None, debug=None):
        logger.info('Starting JitbitApi ..')

        # Rate limiting state - using deque for efficient sliding window
        # Track timestamps of requests in the last minute
        self._request_history_default = deque()  # For standard endpoints (90/min)
        self._request_history_restricted = deque()  # For restricted endpoints (60/min)

        # Restricted endpoints that have lower rate limits
        self._restricted_endpoints = {'/UserByEmail', '/Search'}

        # JitBit user caching - reduces redundant API calls during migration
        # Maps email -> JitBit user_id and user_id -> is_technician status
        self._jitbit_user_id_cache: dict[str, int] = {}  # email (lowercase) -> JitBit user_id
        self._jitbit_technician_cache: dict[int, bool] = {}  # JitBit user_id -> is_technician
        self._jitbit_cache_hits = 0  # Cache statistics
        self._jitbit_cache_misses = 0

    def __del__(self):
        pass

    def _check_rate_limit(self, url: str) -> None:
        """
        Check and enforce rate limits before making a request.
        Uses sliding window approach - removes timestamps older than 1 minute.
        Sleeps if rate limit would be exceeded.

        Args:
            url: The API endpoint URL being called
        """
        current_time = time.time()
        one_minute_ago = current_time - 60

        # Determine which rate limit applies based on endpoint
        is_restricted = any(endpoint in url for endpoint in self._restricted_endpoints)

        if is_restricted:
            history = self._request_history_restricted
            limit = config.JITBIT_RATE_LIMIT_RESTRICTED
            limit_type = "restricted"
        else:
            history = self._request_history_default
            limit = config.JITBIT_RATE_LIMIT_DEFAULT
            limit_type = "default"

        # Remove timestamps older than 1 minute (sliding window)
        while history and history[0] < one_minute_ago:
            history.popleft()

        # Check if we've hit the rate limit
        if len(history) >= limit:
            # Calculate how long to wait until the oldest request expires
            oldest_request = history[0]
            wait_time = 60 - (current_time - oldest_request) + 0.1  # Add small buffer

            if wait_time > 0:
                logger.warning(
                    f'Rate limit ({limit_type}: {limit}/min) reached. '
                    f'Waiting {wait_time:.1f} seconds before next request...'
                )
                time.sleep(wait_time)

                # Clean up expired timestamps after waiting
                current_time = time.time()
                one_minute_ago = current_time - 60
                while history and history[0] < one_minute_ago:
                    history.popleft()

        # Record this request timestamp
        history.append(current_time)

    def _get_auth_config(self) -> tuple[dict | None, dict | None]:
        """
        Get authentication configuration based on auth method.
        Returns (auth, headers) tuple.

        - Basic auth: returns (auth=(user, pwd), None)
        - Token auth: returns (None, headers={'Authorization': 'Bearer token'})
        """
        auth_method = config.JITBIT_AUTH_METHOD

        if auth_method == 'token':
            logger.debug('Using JitBit token authentication')
            return None, {'Authorization': f'Bearer {config.JITBIT_TOKEN}'}
        else:
            # Basic authentication
            logger.debug('Using JitBit basic authentication')
            return (config.JITBIT_USER, config.JITBIT_PWD), None

    def _make_request(self, method: str, url: str, **kwargs):
        """
        Make an authenticated request to JitBit API with rate limiting and retry logic.
        Automatically adds the correct authentication based on config.
        Handles 429 (Too Many Requests) responses with exponential backoff.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            **kwargs: Additional arguments passed to requests.request()

        Returns:
            requests.Response object

        Raises:
            Exception: If request fails after all retry attempts
        """
        max_retries = config.JITBIT_RATE_LIMIT_MAX_RETRIES
        retry_delay = config.JITBIT_RATE_LIMIT_RETRY_DELAY

        for attempt in range(max_retries + 1):
            # Check rate limit before making request
            self._check_rate_limit(url)

            # Get authentication config
            auth, headers = self._get_auth_config()

            # Merge any existing headers
            if headers:
                if 'headers' in kwargs:
                    kwargs['headers'].update(headers)
                else:
                    kwargs['headers'] = headers

            # Add auth if using basic auth
            if auth:
                kwargs['auth'] = auth

            # Make the request
            response = requests.request(method, url, **kwargs)

            # Handle 429 Too Many Requests
            if response.status_code == 429:
                if attempt < max_retries:
                    # Exponential backoff: wait longer on each retry
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(
                        f'Received 429 Too Many Requests. '
                        f'Attempt {attempt + 1}/{max_retries + 1}. '
                        f'Waiting {wait_time} seconds before retry...'
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f'Received 429 Too Many Requests after {max_retries + 1} attempts. '
                        f'Giving up on request to {url}'
                    )
                    return response

            # Success or non-429 error - return the response
            return response

        # Should not reach here, but just in case
        return response

    def check_url_and_user(self) -> bool:

        ret = False
        # Check URL and user authentication
        url = config.JITBIT_API_URL + '/Authorization'
        logger.info(f'Connecting to  URL: {url} ...')

        try:

            response = self._make_request('POST', url)  # Fixed: API requires POST not GET

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

    def post_ticket(self, key: str, category_id: int, subject: str, body: str, priority_id: int, created_by: int,
                    behalf_of: int | None = None, custom_fields: dict[int, str] | None = None) -> int:
        """
        Create a new ticket in JitBit.

        Args:
            key: Jira issue key (for logging)
            category_id: JitBit category ID
            subject: Ticket subject
            body: Ticket body
            priority_id: Priority ID
            created_by: User ID of ticket creator
            behalf_of: Optional user ID to create ticket on behalf of
            custom_fields: Optional dict mapping custom field IDs (int) to values (str)
                          Will be converted to JSON-string format required by JitBit API
                          Example dict: {66782: "Andy Pettit", 12345: "Some Value"}
                          Becomes JSON-string: '{"66782": "Andy Pettit", "12345": "Some Value"}'
                          Note: Keys are CustomFieldId numbers, not field names

        Returns:
            JitBit ticket ID if successful, -1 otherwise
        """
        ret = -1

        url = config.JITBIT_API_URL + '/ticket'
        logger.info(f'[{key}] Connecting to  URL: {url} ...')
        in_data = {
                     'categoryId': category_id,
                     'subject': subject,
                     'body': body,
                     'priorityId': priority_id,
                     'userId': created_by,
                     'suppressConfirmation': True,  # Skip sending user confirmation email
                     'dueDate': ''  # Empty string for dueDate
                  }

        # Add custom fields if provided
        # JitBit API requires customFields as a JSON-string in format: {"CustomFieldId": "value", ...}
        if custom_fields:
            # Convert dict to JSON-string with field IDs as string keys
            custom_fields_json = json.dumps({str(k): v for k, v in custom_fields.items()})
            in_data['customFields'] = custom_fields_json
            logger.debug(f'[{key}] Adding custom fields JSON-string: {custom_fields_json}')

        logger.debug(in_data)

        try:
            response = self._make_request('POST', url, data=in_data)

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
            response = self._make_request('POST', url, data=in_data)

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

        in_data = {'uploadFile': open(attach_file, 'rb')}  # Fixed: API expects 'uploadFile' not 'file'
        try:

            response = self._make_request('POST', url, params=params, files=in_data)

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
        Uses in-memory cache to reduce redundant API calls.
        """
        # Validate email format
        if isinstance(email, int) or not email or not isinstance(email, str):
            logger.warning(f'{email} is not a valid email format, using default email')
            email = config.JITBIT_DEFAULT_ASSIGN_EMAIL

        # Normalize email for cache lookup (case-insensitive)
        email_key = email.lower()

        # Check cache first
        if email_key in self._jitbit_user_id_cache:
            user_id = self._jitbit_user_id_cache[email_key]
            self._jitbit_cache_hits += 1
            logger.debug(f'[{email}] Cache hit - JitBit user_id: {user_id} (hits: {self._jitbit_cache_hits})')
            return user_id

        # Cache miss - make API call
        self._jitbit_cache_misses += 1
        logger.debug(f'[{email}] Cache miss - fetching from API (misses: {self._jitbit_cache_misses})')

        url = config.JITBIT_API_URL + '/UserByEmail'
        params = {'email': email}
        logger.info(f'[{email}] Connecting to  URL: {url} ...')

        try:
            response = self._make_request('GET', url, params=params)

            if response.status_code == 200:
                logger.info(f'[{email}] Successfully connected to URL: {url}')
                user_id = response.json()["UserID"]
                logger.info(f'User ID: {user_id}')

                # Store in cache
                self._jitbit_user_id_cache[email_key] = user_id

                return user_id

            else:
                logger.critical(f'[{email}] ERROR: Unable to connect to URL: {url} - Status {response.status_code}')
                logger.debug(f'Response body: {response.text}')
                # Return default user ID
                default_email_key = config.JITBIT_DEFAULT_ASSIGN_EMAIL.lower()

                # Check if default user is cached
                if default_email_key in self._jitbit_user_id_cache:
                    logger.debug(f'Using cached default user ID')
                    return self._jitbit_user_id_cache[default_email_key]

                default_response = self._make_request(
                    'GET',
                    url,
                    params={'email': config.JITBIT_DEFAULT_ASSIGN_EMAIL}
                )
                if default_response.status_code == 200:
                    default_user_id = default_response.json()["UserID"]
                    # Cache default user too
                    self._jitbit_user_id_cache[default_email_key] = default_user_id
                    return default_user_id
                else:
                    logger.error(f'Default user lookup also failed with status {default_response.status_code}')
                return -1

        except Exception as e:
            logger.critical(str(e))
            raise


    def get_user_is_technician(self, user_id: int) -> bool:
        """
        Check if a user has the technician flag set in JitBit.
        Returns True if user is a technician, False otherwise.
        Uses in-memory cache to reduce redundant API calls.
        """
        # Check cache first
        if user_id in self._jitbit_technician_cache:
            is_tech = self._jitbit_technician_cache[user_id]
            logger.debug(f'[{user_id}] Cache hit - JitBit technician status: {is_tech}')
            return is_tech

        # Cache miss - make API call
        logger.debug(f'[{user_id}] Cache miss - fetching technician status from API')

        url = config.JITBIT_API_URL + '/User'
        params = {'userId': user_id}  # Fixed: API expects 'userId' not 'id'
        logger.info(f'[{user_id}] Checking technician status at URL: {url} ...')

        try:
            response = self._make_request('GET', url, params=params)

            if response.status_code == 200:
                logger.info(f'[{user_id}] Successfully retrieved user info from URL: {url}')
                user_data = response.json()
                is_tech = user_data.get("IsTech", False)  # Fixed: API returns 'IsTech' not 'IsTechie'
                logger.info(f'User {user_id} technician status: {is_tech}')

                # Store in cache
                self._jitbit_technician_cache[user_id] = is_tech

                return is_tech
            else:
                logger.warning(f'[{user_id}] ERROR: Unable to retrieve user info from URL: {url} - Status {response.status_code}')
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
            response = self._make_request('POST', url, params=params)

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
        - closeDate: Closed date (only for resolved/closed tickets)
        - categoryId or newCategoryId: Category
        - priorityId: Priority
        - statusId: Status
        - dueDate: Due date
        - tags: Tags
        - subject: Subject
        - body: Body
        - timeSpentInSeconds: Time spent

        Example: post_update_ticket('KEY-1', 123, assignedUserId=5, date='2023-01-01', closeDate='2023-01-05')
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
            response = self._make_request('POST', url, data=in_data)

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
            response = self._make_request('GET', url, data=in_data)

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
            response = self._make_request('GET', url)

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
            response = self._make_request('GET', url)

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

        Note: is_technician parameter is ignored as JitBit assigns technician permissions
              per-category via AddCategoryTechPermission API, not during user creation.
        """
        url = config.JITBIT_API_URL + '/CreateUser'
        logger.info(f'Creating user: {email}')

        in_data = {
            'email': email,
            'firstName': first_name,
            'lastName': last_name
        }

        try:
            response = self._make_request('POST', url, data=in_data)

            if response.status_code == 200:
                user_id = int(response.text)
                logger.info(f'Successfully created user {email} with ID {user_id}')
                return user_id
            else:
                logger.error(f'ERROR: Unable to create user: {response.status_code}')
                logger.error(f'Response: {response.text}')
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

