import json
import requests
from pprint import pp

class PlexClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.headers = {
            'X-Plex-Token': self.token,
            'Accept': 'application/json'
        }
        sections_url = f'{base_url}/library/sections/all'

    def get_library_sections(self):
        url = f"{self.base_url}/library/sections"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return { section['title']: section['key'] for section in response.json().get('MediaContainer', {}).get('Directory', []) }
    
    def get_library_size(self, section_key):
        url = f"{self.base_url}/library/sections/{section_key}/all"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get('MediaContainer', {}).get('size', 0)

    def empty_section_trash(self, section_key):
        url = f"{self.base_url}/library/sections/{section_key}/emptyTrash"
        response = requests.put(url, headers=self.headers)
        response.raise_for_status()
        return response.status_code == 200

if __name__ == "__main__":
    # Example usage / testing
    import dotenv
    dotenv.load_dotenv('data/.env')
    from os import getenv
    
    plex = PlexClient(base_url=getenv('PLEX_URL'), token=getenv('PLEX_TOKEN'))
    sections = plex.get_library_sections()
    plex.empty_section_trash(sections['Movies'])
    plex.empty_section_trash(sections['TV Shows'])
    pp(sections)
    for key, value in sections.items():
        size = plex.get_library_size(value)
        print(f'Section: {key}, Size: {size}')