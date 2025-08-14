# api_client.py
import time
import jwt
import requests

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.refresh_token = None

    def login(self, username, password):
        """Login and store tokens."""
        resp = requests.post(
            f"{self.base_url}/api_slc/login_check",
            json={"username": username, "password": password},
            verify=False
        )
        resp.raise_for_status()
        data = resp.json()
        self.token = data["token"]
        self.refresh_token = data["refresh_token"]

    def will_expire_soon(self, seconds=300):
        if not self.token:
            return True
        try:
            decoded = jwt.decode(self.token, options={"verify_signature": False})
            return decoded["exp"] < time.time() + seconds
        except Exception:
            return True

    def refresh(self):
        if not self.refresh_token:
            raise RuntimeError("No refresh token available")
        resp = requests.post(
            f"{self.base_url}/api/auth/refresh",
            json={"refresh_token": self.refresh_token},
            verify=False
        )
        resp.raise_for_status()
        data = resp.json()
        self.token = data["token"]
        self.refresh_token = data["refresh_token"]

    def request(self, method, endpoint, **kwargs):
        # Auto refresh if needed
        if self.will_expire_soon():
            self.refresh()

        headers = kwargs.pop("headers", {})
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        kwargs["headers"] = headers

        resp = requests.request(method, f"{self.base_url}{endpoint}", **kwargs)

        if resp.status_code == 401:
            self.refresh()
            headers["Authorization"] = f"Bearer {self.token}"
            kwargs["headers"] = headers
            resp = requests.request(method, f"{self.base_url}{endpoint}", **kwargs)

        return resp
