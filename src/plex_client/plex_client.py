import json
import requests
from pprint import pp


class PlexClient:
    def __init__(self, base_url, token):
        """Initialize PlexClient with base URL and authentication token.
        
        Args:
            base_url: The base URL of the Plex server.
            token: The authentication token for Plex API.
            
        Raises:
            ValueError: If base_url or token is None or empty.
        """
        if not base_url:
            raise ValueError("base_url must be provided and non-empty")
        if not token:
            raise ValueError("token must be provided and non-empty")
            
        self.base_url = base_url
        self.token = token
        self.headers = {
            'X-Plex-Token': self.token,
            'Accept': 'application/json'
        }

    def get_library_sections(self):
        """Get all library sections from Plex server.
        
        Returns:
            dict: Dictionary mapping section titles to their keys.
            
        Raises:
            requests.exceptions.RequestException: If the HTTP request fails.
        """
        url = f"{self.base_url}/library/sections"
        try:
            response = requests.get(url, headers=self.headers)
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
            response = requests.get(url, headers=self.headers)
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
            response = requests.put(url, headers=self.headers)
            response.raise_for_status()
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(
                f"Failed to empty trash for section {section_key}: {e}"
            ) from e

if __name__ == "__main__":
    # Example usage / testing
    from os import getenv
    
    plex = PlexClient(base_url=getenv('PLEX_URL'), token=getenv('PLEX_TOKEN'))
    sections = plex.get_library_sections()
    plex.empty_section_trash(sections['Movies'])
    plex.empty_section_trash(sections['TV Shows'])
    pp(sections)
    for key, value in sections.items():
        size = plex.get_library_size(value)
        print(f'Section: {key}, Size: {size}')