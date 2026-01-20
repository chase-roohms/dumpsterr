"""
Unit tests for plex_client module.
"""
import pytest
import responses
import requests
from unittest.mock import Mock, patch

import plex_client.plex_client as plex_module


class TestPlexClientInit:
    """Tests for PlexClient initialization."""
    
    def test_init_with_valid_parameters(self):
        """Test initialization with valid parameters."""
        client = plex_module.PlexClient(
            base_url='http://localhost:32400',
            token='test_token'
        )
        assert client.base_url == 'http://localhost:32400'
        assert client.token == 'test_token'
        assert client.timeout == 10  # Default
        assert 'X-Plex-Token' in client.headers
        assert client.headers['X-Plex-Token'] == 'test_token'
        assert client.headers['Accept'] == 'application/json'
    
    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        client = plex_module.PlexClient(
            base_url='http://localhost:32400',
            token='test_token',
            timeout=30
        )
        assert client.timeout == 30
    
    def test_init_with_custom_retries(self):
        """Test initialization with custom max_retries."""
        client = plex_module.PlexClient(
            base_url='http://localhost:32400',
            token='test_token',
            max_retries=5
        )
        # Can't directly test retry count, but verify initialization succeeds
        assert client is not None
    
    def test_init_without_base_url(self):
        """Test initialization without base_url raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            plex_module.PlexClient(base_url='', token='test_token')
        assert 'base_url must be provided' in str(exc_info.value)
    
    def test_init_without_token(self):
        """Test initialization without token raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            plex_module.PlexClient(base_url='http://localhost:32400', token='')
        assert 'token must be provided' in str(exc_info.value)
    
    def test_init_with_none_base_url(self):
        """Test initialization with None base_url."""
        with pytest.raises(ValueError):
            plex_module.PlexClient(base_url=None, token='test_token')
    
    def test_init_with_none_token(self):
        """Test initialization with None token."""
        with pytest.raises(ValueError):
            plex_module.PlexClient(base_url='http://localhost:32400', token=None)


class TestGetLibrarySections:
    """Tests for get_library_sections method."""
    
    @responses.activate
    def test_get_library_sections_success(self):
        """Test successfully retrieving library sections."""
        responses.add(
            responses.GET,
            'http://localhost:32400/library/sections',
            json={
                'MediaContainer': {
                    'Directory': [
                        {'title': 'Movies', 'key': '1'},
                        {'title': 'TV Shows', 'key': '2'},
                        {'title': 'Music', 'key': '3'}
                    ]
                }
            },
            status=200
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        sections = client.get_library_sections()
        
        assert sections == {
            'Movies': '1',
            'TV Shows': '2',
            'Music': '3'
        }
    
    @responses.activate
    def test_get_library_sections_empty(self):
        """Test retrieving library sections when none exist."""
        responses.add(
            responses.GET,
            'http://localhost:32400/library/sections',
            json={'MediaContainer': {'Directory': []}},
            status=200
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        sections = client.get_library_sections()
        
        assert sections == {}
    
    @responses.activate
    def test_get_library_sections_no_directory_key(self):
        """Test when response doesn't have Directory key."""
        responses.add(
            responses.GET,
            'http://localhost:32400/library/sections',
            json={'MediaContainer': {}},
            status=200
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        sections = client.get_library_sections()
        
        assert sections == {}
    
    @responses.activate
    def test_get_library_sections_http_error(self):
        """Test handling HTTP errors."""
        responses.add(
            responses.GET,
            'http://localhost:32400/library/sections',
            status=500
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        with pytest.raises(requests.exceptions.RequestException) as exc_info:
            client.get_library_sections()
        assert 'Failed to retrieve library sections' in str(exc_info.value)
    
    @responses.activate
    def test_get_library_sections_unauthorized(self):
        """Test handling unauthorized access."""
        responses.add(
            responses.GET,
            'http://localhost:32400/library/sections',
            status=401
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        with pytest.raises(requests.exceptions.RequestException):
            client.get_library_sections()
    
    @responses.activate
    def test_get_library_sections_timeout(self):
        """Test handling timeout."""
        responses.add(
            responses.GET,
            'http://localhost:32400/library/sections',
            body=requests.exceptions.Timeout()
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        with pytest.raises(requests.exceptions.RequestException):
            client.get_library_sections()
    
    @responses.activate
    def test_get_library_sections_includes_headers(self):
        """Test that request includes proper headers."""
        def request_callback(request):
            assert 'X-Plex-Token' in request.headers
            assert request.headers['X-Plex-Token'] == 'test_token'
            assert request.headers['Accept'] == 'application/json'
            return (200, {}, '{"MediaContainer": {"Directory": []}}')
        
        responses.add_callback(
            responses.GET,
            'http://localhost:32400/library/sections',
            callback=request_callback
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        client.get_library_sections()


class TestGetLibrarySize:
    """Tests for get_library_size method."""
    
    @responses.activate
    def test_get_library_size_success(self):
        """Test successfully getting library size."""
        responses.add(
            responses.GET,
            'http://localhost:32400/library/sections/1/all',
            json={'MediaContainer': {'size': 1234}},
            status=200
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        size = client.get_library_size('1')
        
        assert size == 1234
    
    @responses.activate
    def test_get_library_size_zero(self):
        """Test getting size of empty library."""
        responses.add(
            responses.GET,
            'http://localhost:32400/library/sections/1/all',
            json={'MediaContainer': {'size': 0}},
            status=200
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        size = client.get_library_size('1')
        
        assert size == 0
    
    @responses.activate
    def test_get_library_size_missing_size_key(self):
        """Test when response doesn't have size key."""
        responses.add(
            responses.GET,
            'http://localhost:32400/library/sections/1/all',
            json={'MediaContainer': {}},
            status=200
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        size = client.get_library_size('1')
        
        assert size == 0  # Default value
    
    @responses.activate
    def test_get_library_size_http_error(self):
        """Test handling HTTP errors."""
        responses.add(
            responses.GET,
            'http://localhost:32400/library/sections/1/all',
            status=404
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        with pytest.raises(requests.exceptions.RequestException) as exc_info:
            client.get_library_size('1')
        assert 'Failed to retrieve library size' in str(exc_info.value)
    
    @responses.activate
    def test_get_library_size_different_sections(self):
        """Test getting size for different section keys."""
        responses.add(
            responses.GET,
            'http://localhost:32400/library/sections/1/all',
            json={'MediaContainer': {'size': 100}},
            status=200
        )
        responses.add(
            responses.GET,
            'http://localhost:32400/library/sections/2/all',
            json={'MediaContainer': {'size': 200}},
            status=200
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        size1 = client.get_library_size('1')
        size2 = client.get_library_size('2')
        
        assert size1 == 100
        assert size2 == 200


class TestEmptySectionTrash:
    """Tests for empty_section_trash method."""
    
    @responses.activate
    def test_empty_trash_success(self):
        """Test successfully emptying trash."""
        responses.add(
            responses.PUT,
            'http://localhost:32400/library/sections/1/emptyTrash',
            status=200
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        result = client.empty_section_trash('1')
        
        assert result is True
    
    @responses.activate
    def test_empty_trash_non_200_status(self):
        """Test emptying trash with non-200 response."""
        responses.add(
            responses.PUT,
            'http://localhost:32400/library/sections/1/emptyTrash',
            status=204  # Some servers return 204
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        result = client.empty_section_trash('1')
        
        assert result is False
    
    @responses.activate
    def test_empty_trash_http_error(self):
        """Test handling HTTP errors."""
        responses.add(
            responses.PUT,
            'http://localhost:32400/library/sections/1/emptyTrash',
            status=500
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        with pytest.raises(requests.exceptions.RequestException) as exc_info:
            client.empty_section_trash('1')
        assert 'Failed to empty trash' in str(exc_info.value)
    
    @responses.activate
    def test_empty_trash_unauthorized(self):
        """Test handling unauthorized access."""
        responses.add(
            responses.PUT,
            'http://localhost:32400/library/sections/1/emptyTrash',
            status=401
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        with pytest.raises(requests.exceptions.RequestException):
            client.empty_section_trash('1')
    
    @responses.activate
    def test_empty_trash_uses_put_method(self):
        """Test that empty trash uses PUT method."""
        def request_callback(request):
            # This will only be called if the method matches
            return (200, {}, '')
        
        responses.add_callback(
            responses.PUT,
            'http://localhost:32400/library/sections/1/emptyTrash',
            callback=request_callback
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        result = client.empty_section_trash('1')
        assert result is True
    
    @responses.activate
    def test_empty_trash_multiple_sections(self):
        """Test emptying trash for multiple sections."""
        responses.add(
            responses.PUT,
            'http://localhost:32400/library/sections/1/emptyTrash',
            status=200
        )
        responses.add(
            responses.PUT,
            'http://localhost:32400/library/sections/2/emptyTrash',
            status=200
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        result1 = client.empty_section_trash('1')
        result2 = client.empty_section_trash('2')
        
        assert result1 is True
        assert result2 is True


class TestPlexClientRetry:
    """Tests for retry behavior."""
    
    @responses.activate
    def test_retry_on_503(self):
        """Test that client retries on 503 error."""
        # First two calls fail, third succeeds
        responses.add(responses.GET, 'http://localhost:32400/library/sections', status=503)
        responses.add(responses.GET, 'http://localhost:32400/library/sections', status=503)
        responses.add(
            responses.GET,
            'http://localhost:32400/library/sections',
            json={'MediaContainer': {'Directory': []}},
            status=200
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token', max_retries=3)
        sections = client.get_library_sections()
        
        assert sections == {}
    
    @responses.activate
    def test_exhausted_retries(self):
        """Test that client raises after exhausting retries."""
        # All attempts fail
        for _ in range(5):
            responses.add(
                responses.GET,
                'http://localhost:32400/library/sections',
                status=503
            )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token', max_retries=2)
        with pytest.raises(requests.exceptions.RequestException):
            client.get_library_sections()


@pytest.mark.plex
class TestPlexClientIntegration:
    """Integration tests with real Plex server. Requires .env.test configuration."""
    
    def test_real_plex_connection(self, plex_env_vars):
        """Test connecting to real Plex server."""
        client = plex_module.PlexClient(
            base_url=plex_env_vars['url'],
            token=plex_env_vars['token']
        )
        
        # Should not raise
        sections = client.get_library_sections()
        assert isinstance(sections, dict)
    
    def test_real_plex_get_sections(self, plex_env_vars):
        """Test getting library sections from real Plex server."""
        client = plex_module.PlexClient(
            base_url=plex_env_vars['url'],
            token=plex_env_vars['token']
        )
        
        sections = client.get_library_sections()
        
        # Should return dictionary with at least some sections
        assert isinstance(sections, dict)
        # At minimum, check structure is correct
        for title, key in sections.items():
            assert isinstance(title, str)
            assert isinstance(key, str)
    
    def test_real_plex_get_library_size(self, plex_env_vars):
        """Test getting library size from real Plex server."""
        client = plex_module.PlexClient(
            base_url=plex_env_vars['url'],
            token=plex_env_vars['token']
        )
        
        sections = client.get_library_sections()
        if sections:
            # Get size of first section
            first_key = list(sections.values())[0]
            size = client.get_library_size(first_key)
            
            assert isinstance(size, int)
            assert size >= 0


class TestPlexClientEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_client_with_trailing_slash_in_url(self):
        """Test that trailing slash in base_url is handled."""
        client = plex_module.PlexClient('http://localhost:32400/', 'test_token')
        assert client.base_url == 'http://localhost:32400/'
    
    @responses.activate
    def test_malformed_json_response(self):
        """Test handling malformed JSON response."""
        responses.add(
            responses.GET,
            'http://localhost:32400/library/sections',
            body='not valid json',
            status=200
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        with pytest.raises(Exception):  # Will raise JSONDecodeError or similar
            client.get_library_sections()
    
    @responses.activate
    def test_unexpected_response_structure(self):
        """Test handling unexpected response structure."""
        responses.add(
            responses.GET,
            'http://localhost:32400/library/sections',
            json={'unexpected': 'structure'},
            status=200
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        sections = client.get_library_sections()
        
        # Should return empty dict, not crash
        assert sections == {}
    
    def test_client_session_persistence(self):
        """Test that session is reused across requests."""
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        session1 = client.session
        
        # Accessing session again should return same instance
        session2 = client.session
        assert session1 is session2
    
    @responses.activate
    def test_special_characters_in_section_names(self):
        """Test handling special characters in section names."""
        responses.add(
            responses.GET,
            'http://localhost:32400/library/sections',
            json={
                'MediaContainer': {
                    'Directory': [
                        {'title': 'Movies & TV', 'key': '1'},
                        {'title': 'Kids\' Shows', 'key': '2'},
                        {'title': 'Docs/Educational', 'key': '3'}
                    ]
                }
            },
            status=200
        )
        
        client = plex_module.PlexClient('http://localhost:32400', 'test_token')
        sections = client.get_library_sections()
        
        assert 'Movies & TV' in sections
        assert 'Kids\' Shows' in sections
        assert 'Docs/Educational' in sections
