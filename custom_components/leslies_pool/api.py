"""API client for Leslie's Pool Water Tests."""

import requests
from bs4 import BeautifulSoup
from bs4 import Tag


class LesliesPoolApi:
    """API class to interact with Leslie's Pool service."""

    LOGIN_PAGE_URL = "https://lesliespool.com/on/demandware.store/Sites-lpm_site-Site/en_US/Account-Show"
    LOGIN_URL = "https://lesliespool.com/on/demandware.store/Sites-lpm_site-Site/en_US/Account-Login"
    WATER_TEST_URL = "https://lesliespool.com/on/demandware.store/Sites-lpm_site-Site/en_US/WaterTest-GetWaterTest"

    def __init__(
        self, username: str, password: str, pool_profile_id: str, pool_name: str
    ) -> None:
        """Initialize the API with user credentials and pool details."""
        self.username = username
        self.password = password
        self.pool_profile_id = pool_profile_id
        self.pool_name = pool_name
        self.session = requests.Session()
        self._last_successful_values = {}  # Cache to store last valid data
        self._last_successful_fetch = None  # Timestamp of last successful fetch

    def authenticate(self) -> bool:
        """Authenticate the user and start a session."""
        response = self.session.get(self.LOGIN_PAGE_URL)
        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token_tag = soup.find("input", {"name": "csrf_token"})

        csrf_token = None
        if isinstance(csrf_token_tag, Tag) and csrf_token_tag.has_attr("value"):
            csrf_token = csrf_token_tag["value"]

        if not csrf_token:
            return False

        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "user-agent": "Mozilla/5.0",
        }

        payload = {
            "loginEmail": self.username,
            "loginPassword": self.password,
            "csrf_token": csrf_token,
        }

        login_response = self.session.post(
            self.LOGIN_URL, headers=headers, data=payload
        )
        return login_response.status_code == 200

    def fetch_water_test_data(self) -> dict:
        """Fetch water test data for the pool."""
        import json
        import logging

        _LOGGER = logging.getLogger(__name__)
        _LOGGER.debug("Fetching water test data")
        
        # Try to fetch the data with authentication retry logic
        for attempt in range(1, 3):  # Try up to 2 times
            try:
                # Check if we need to authenticate first
                if attempt > 1:
                    _LOGGER.info(f"Authentication attempt {attempt}")
                    if not self.authenticate():
                        _LOGGER.error("Authentication failed")
                        return {}
                
                # First navigate to the water test page to set up session and cookies
                landing_response = self.session.get(
                    f"https://lesliespool.com/on/demandware.store/Sites-lpm_site-Site/en_US/WaterTest-Landing?poolProfileId={self.pool_profile_id}&poolName={self.pool_name}"
                )
                
                # Check if we were redirected to the login page
                if "Account-Show" in landing_response.url or "login?rurl=1" in landing_response.url:
                    _LOGGER.warning("Session expired, need to re-authenticate")
                    if attempt < 2:  # Only try to authenticate once
                        continue  # Skip to next attempt which will authenticate
                    else:
                        _LOGGER.error("Failed to maintain authenticated session")
                        return {}
                
                cookies = self.session.cookies.get_dict()
                cookie_header = "; ".join([f"{key}={value}" for key, value in cookies.items()])
                
                headers = {
                    "accept": "application/json, text/javascript, */*; q=0.01",
                    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "cookie": cookie_header,
                    "user-agent": "Mozilla/5.0",
                }
                
                payload = "poolProfileName=Pool&poolSanitizer=Salt+3000-4000"
                _LOGGER.debug(f"Sending POST request to {self.WATER_TEST_URL}")
                response = self.session.post(self.WATER_TEST_URL, headers=headers, data=payload)
                
                # Check HTTP status code
                if response.status_code != 200:
                    _LOGGER.error(f"HTTP error: {response.status_code}")
                    if attempt < 2:
                        continue  # Try again with authentication
                    return {}
                
                # Try to parse JSON response
                try:
                    # Get a sample of the response for debugging
                    response_preview = response.text[:200] + "..." if len(response.text) > 200 else response.text
                    _LOGGER.debug(f"Response preview: {response_preview}")
                    
                    data = response.json()
                    
                    # Check for authentication issues in the JSON response
                    if "errorMsg" in data:
                        _LOGGER.error(f"API returned error: {data.get('errorMsg')}")
                        if "login" in str(data.get('errorMsg')).lower() and attempt < 2:
                            _LOGGER.warning("Authentication error detected in response, re-authenticating")
                            if self.authenticate():
                                continue
                    
                    break  # Successfully parsed JSON, exit the loop
                except json.JSONDecodeError as e:
                    _LOGGER.error(f"JSON parsing error: {e}")
                    _LOGGER.debug(f"Response content (first 500 chars): {response.text[:500]}")
                    
                    # Check if this looks like an auth issue (e.g., HTML login page)
                    if "<html" in response.text[:100].lower():
                        _LOGGER.warning("Response appears to be HTML instead of JSON - likely an auth issue")
                        # Look for login-related indicators in the response
                        if any(sign in response.text.lower() for sign in ["login", "sign in", "password", "username"]):
                            _LOGGER.info("Login page detected in response - session likely expired")
                        if attempt < 2:  # Try re-authenticating
                            if self.authenticate():
                                continue
                    
                    return {}  # If all attempts failed or not an auth issue
            
            except requests.RequestException as e:
                _LOGGER.error(f"Request failed: {e}")
                if attempt < 2:
                    _LOGGER.info("Retrying after connection error")
                    continue
                return {}
        
            # If we've exhausted all retries without success
            if 'data' not in locals():
                _LOGGER.error("Failed to fetch data after all retries")
                if self._last_successful_values:
                    _LOGGER.info("Returning last cached values due to fetch failure")
                    return self._last_successful_values
                return {}

        # Process the data if we successfully retrieved it
        values = {}
        try:
            # Check if the response contains the expected HTML content
            if "response" not in data:
                _LOGGER.error("Missing 'response' key in JSON data")
                return {}
                
            html_content = data["response"]
            _LOGGER.debug(f"HTML content length: {len(html_content)}")
            
            soup = BeautifulSoup(html_content, "html.parser")
            # Original find syntax that was working before
            table = soup.find(
                "table", {"class": "table table-striped table-bordered table-hover table-sm"}
            )
            
            if not isinstance(table, Tag):
                _LOGGER.warning("Water test table not found in response")
                if self._last_successful_values:
                    _LOGGER.info("Returning last cached values since no water test table was found")
                    return self._last_successful_values
                return {}
            first_row_tag = table.find("tbody")
            if isinstance(first_row_tag, Tag):
                first_row = first_row_tag.find("tr")
                if isinstance(first_row, Tag):
                    columns = first_row.find_all("td")
                    if len(columns) > 10:
                        # Extract test_date from the first column
                        test_date_tag = first_row.find(
                            "th", {"class": "text-center align-middle p-1"}
                        )
                        test_date = None
                        if test_date_tag:
                            badge = test_date_tag.find(
                                "span", {"class": "badge badge-secondary p-2"}
                            )
                            if badge:
                                test_date = badge.text.strip()

                        # Determine in_store value from the last column
                        in_store_tag = first_row.find_all("td")[-1]
                        in_store = True  # Default to True
                        if in_store_tag and in_store_tag.find(
                            "i", {"class": "fa fa-times-circle text-danger"}
                        ):
                            in_store = False

                        # Populate the values dictionary
                        values = {
                            "free_chlorine": columns[1].text.strip(),
                            "total_chlorine": columns[2].text.strip(),
                            "ph": columns[3].text.strip(),
                            "alkalinity": columns[4].text.strip(),
                            "calcium": columns[5].text.strip(),
                            "cyanuric_acid": columns[6].text.strip(),
                            "iron": columns[7].text.strip(),
                            "copper": columns[8].text.strip(),
                            "phosphates": columns[9].text.strip(),
                            "salt": columns[10].text.strip(),
                            "test_date": test_date,
                            "in_store": in_store,
                        }

        except Exception as e:
            _LOGGER.error(f"Error processing HTML content: {e}")
            return {}
            
        # If we successfully got values, cache them for future use if needed
        if values:
            import time
            self._last_successful_values = values.copy()
            self._last_successful_fetch = time.time()
            _LOGGER.debug("Successfully updated cache with new values")
        
        return values
