import os
import requests
from requests.auth import HTTPBasicAuth
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

class ConfluenceClient:
    def __init__(self, base_url="https://kms.wam-sso.bosch.com/rest/api/content/"):
        self.base_url = base_url
        self.username = os.getenv("COMPASS_API_USERNAME")
        self.password = os.getenv("COMPASS_API_PASSWORD")
        
        # Configure robust HTTP session with automatic connection pooling and retries
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10))

    def get_auth(self):
        if not self.username or not self.password:
            raise ValueError("Missing environment variables COMPASS_API_USERNAME or COMPASS_API_PASSWORD.")
        return HTTPBasicAuth(self.username, self.password)

    def fetch_page_html(self, page_id):
        url = f"{self.base_url}{page_id}"
        response = self.session.get(
            url,
            auth=self.get_auth(),
            params={"expand": "body.view"},
            verify=False # Bypasses SSL strictness for corporate handshakes
        )
        if response.status_code != 200:
            raise RuntimeError(f"Confluence API returned {response.status_code}")
        
        data = response.json()
        return data.get("body", {}).get("view", {}).get("value", "")

    def fetch_child_pages(self, parent_id):
        url = f"{self.base_url}{parent_id}/child/page"
        results = []
        params = {"limit": 200}
        
        while url:
            response = self.session.get(url, auth=self.get_auth(), params=params, verify=False)
            if response.status_code != 200:
                raise RuntimeError(f"Confluence API returned {response.status_code}")
            
            data = response.json()
            results.extend(data.get("results", []))
            
            # Follow Confluence API pagination link next
            next_link = data.get("_links", {}).get("next", "")
            if next_link:
                url = f"https://kms.wam-sso.bosch.com{next_link}"
                params = {} # limit is already embedded in next_link
            else:
                url = None
                
        return results
