import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class PlexClient:
    def __init__(self, base_url, token, timeout=10, max_retries=3):
        """Initialize PlexClient with base URL and authentication token.
        
        Args:
            base_url: The base URL of the Plex server.
            token: The authentication token for Plex API.
            timeout: Request timeout in seconds (default: 10).
            max_retries: Maximum number of retry attempts for failed requests (default: 3).
            
        Raises:
            ValueError: If base_url or token is None or empty.
        """
        if not base_url:
            raise ValueError("base_url must be provided and non-empty")
        if not token:
            raise ValueError("token must be provided and non-empty")
            
        self.base_url = base_url
        self.token = token
        self.timeout = timeout
        self.headers = {
            'X-Plex-Token': self.token,
            'Accept': 'application/json'
        }
        
        # Configure retry strategy for transient failures
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,  # Wait 1s, 2s, 4s between retries
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP status codes
            allowed_methods=["GET", "PUT"]  # Retry safe methods
        )
        
        # Create session with retry adapter
        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def get_library_sections(self):
        """Get all library sections from Plex server.
        
        Returns:
            dict: Dictionary mapping section titles to their keys.
            
        Raises:
            requests.exceptions.RequestException: If the HTTP request fails.
        """
        url = f"{self.base_url}/library/sections"
        try:
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return {section['title']: section['key'] 
                    for section in response.json().get('MediaContainer', {}).get('Directory', [])}
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed to retrieve library sections: {e}"
            ) from e
    
    def get_library_size(self, section_key):
        """Get the size of a specific library section.
        
        Args:
            section_key: The key identifier for the library section.
            
        Returns:
            int: Number of items in the library section.
            
        Raises:
            requests.exceptions.RequestException: If the HTTP request fails.
        """
        url = f"{self.base_url}/library/sections/{section_key}/all"
        try:
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json().get('MediaContainer', {}).get('size', 0)
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed to retrieve library size for section {section_key}: {e}"
            ) from e

    def empty_section_trash(self, section_key):
        """Empty the trash for a specific library section.
        
        Args:
            section_key: The key identifier for the library section.
            
        Returns:
            bool: True if successful, False otherwise.
            
        Raises:
            requests.exceptions.RequestException: If the HTTP request fails.
        """
        url = f"{self.base_url}/library/sections/{section_key}/emptyTrash"
        try:
            response = self.session.put(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed to empty trash for section {section_key}: {e}"
            ) from e