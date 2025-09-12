import os
import socket
import ssl
from urllib.parse import urlparse

import certifi
import requests
from requests.adapters import HTTPAdapter


class SSLAdapter(HTTPAdapter):
    """HTTPS adapter that allows dynamic CA bundle injection."""

    def __init__(self, cafile=None, *args, **kwargs):
        self.cafile = cafile
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.load_verify_locations(cafile=certifi.where())
        if self.cafile and os.path.exists(self.cafile):
            context.load_verify_locations(cafile=self.cafile)
        kwargs["ssl_context"] = context
        return super().init_poolmanager(*args, **kwargs)


class AICosmosClient:
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        certs_dir: str = None,
        auto_trust: bool = False,
    ):
        """
        :param base_url: API base URL, e.g. 'https://aicosmos.ai/api'
        :param username: Username for login
        :param password: Password for login
        :param certs_dir: Directory for storing trusted self-signed certs
        :param auto_trust: If True, will automatically trust self-signed certs
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.access_token: str = None
        self.auto_trust = auto_trust

        host = urlparse(self.base_url).hostname
        self.certs_dir = certs_dir or os.path.join(
            os.path.expanduser("~"), ".aicosmos", "certs"
        )
        os.makedirs(self.certs_dir, exist_ok=True)
        self.cert_file = os.path.join(self.certs_dir, f"{host}.pem")

        self.session = requests.Session()
        self.session.mount("https://", SSLAdapter(cafile=self.cert_file))

        self._login()

    def _fetch_server_cert(self, hostname, port=443):
        """Download server's SSL certificate and save locally."""
        pem_path = self.cert_file
        conn = socket.create_connection((hostname, port))
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        with context.wrap_socket(conn, server_hostname=hostname) as sock:
            der_cert = sock.getpeercert(True)
            pem_cert = ssl.DER_cert_to_PEM_cert(der_cert)
            with open(pem_path, "w") as f:
                f.write(pem_cert)
        return pem_path

    def _robust_request(self, method, url, **kwargs):
        try:
            return self.session.request(method, url, **kwargs)
        except requests.exceptions.SSLError as e:
            if not self.auto_trust:
                raise RuntimeError(
                    f"SSL verification failed for {url}. "
                    f"Set auto_trust=True to accept and store the server's certificate."
                ) from e
            host = urlparse(self.base_url).hostname
            self._fetch_server_cert(host)
            self.session.mount("https://", SSLAdapter(cafile=self.cert_file))
            return self.session.request(method, url, **kwargs)

    def _login(self):
        login_data = {
            "username": self.username,
            "password": self.password,
            "grant_type": "password",
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = self._robust_request(
            "POST", f"{self.base_url}/user/login", data=login_data, headers=headers
        )
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data["access_token"]
        else:
            raise ValueError(f"Login failed: {response.status_code} {response.text}")

    def _get_auth_headers(self):
        if not self.access_token:
            raise ValueError("Not logged in")
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _get_session_status(self, session_id):
        response = self._robust_request(
            "GET",
            f"{self.base_url}/sessions/{session_id}/status",
            headers=self._get_auth_headers(),
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Status code: {response.status_code}")

    def create_session(self):
        response = self._robust_request(
            "POST",
            f"{self.base_url}/sessions/create",
            headers=self._get_auth_headers(),
        )
        if response.status_code == 200:
            return response.json()["session_id"]
        else:
            raise ValueError(f"Status code: {response.status_code}")

    def delete_session(self, session_id: str):
        response = self._robust_request(
            "DELETE",
            f"{self.base_url}/sessions/{session_id}",
            headers=self._get_auth_headers(),
        )
        if response.status_code != 200:
            raise ValueError(f"Status code: {response.status_code}")

    def get_my_sessions(self):
        response = self._robust_request(
            "GET",
            f"{self.base_url}/sessions/my_sessions",
            headers=self._get_auth_headers(),
        )
        if response.status_code == 200:
            sessions = response.json()
            self.active_sessions = sessions
            return [
                {
                    "session_id": s["session_id"],
                    "title": s["environment_info"].get("title"),
                }
                for s in sessions
            ]
        else:
            raise ValueError(f"Status code: {response.status_code}")

    def get_session_history(self, session_id: str):
        session = self._get_session_status(session_id)
        return session.get("conversation", [])

    def chat(self, session_id: str, prompt: str):
        data = {"user_input": prompt, "session_id": session_id}
        response = self._robust_request(
            "POST",
            f"{self.base_url}/chat",
            json=data,
            headers=self._get_auth_headers(),
        )
        if response.status_code == 200:
            return response.json()["conversation_history"]
        else:
            raise ValueError(f"Status code: {response.status_code}")
