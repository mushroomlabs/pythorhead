import logging
from enum import Enum
from typing import Optional

import requests

from pythorhead.auth import Authentication

logger = logging.getLogger(__name__)


class Request(Enum):
    GET = "GET"
    PUT = "PUT"
    POST = "POST"


REQUEST_MAP = {
    Request.GET: requests.get,
    Request.PUT: requests.put,
    Request.POST: requests.post,
}


class Requestor:
    nodeinfo: Optional[dict] = None
    raise_exceptions: Optional[bool] = False

    def __init__(self, instance_url, raise_exceptions=False):
        self._auth = Authentication()
        self.raise_exceptions = raise_exceptions
        self.instance_url = instance_url

        try:
            headers = {
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "cross-site",
                "Sec-Fetch-User": "?1",
                "Sec-GPC": "1",
                "User-Agent": "pythorhead/0.5",
            }
            self.nodeinfo = requests.get(f"{self.instance_url}/nodeinfo/2.0.json", headers=headers, timeout=2).json()
        except Exception as err:
            if not self.raise_exceptions:
                logger.error(f"Problem encountered retrieving Lemmy nodeinfo: {err}")
                return
            raise err
        software = self.nodeinfo.get("software", {}).get("name")
        if software != "lemmy":
            logger.error(f"Domain name does not appear to contain a lemmy software, but instead '{software}")
            return
        logger.info(
            f"Connected succesfully to Lemmy v{self.nodeinfo['software']['version']} instance {self.instance_url}"
        )

    @property
    def api_url(self):
        return f"{self.instance_url}/api/v3"

    def api(self, method: Request, endpoint: str, **kwargs) -> Optional[dict]:
        logger.info(f"Requesting API {method} {endpoint}")
        full_url = f"{self.api_url}{endpoint}"
        if self._auth.token:
            if (data := kwargs.get("json")) is not None:
                data["auth"] = self._auth.token
            if (data := kwargs.get("params")) is not None:
                data["auth"] = self._auth.token
        try:
            headers = {
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Sec-GPC": "1",
                "User-Agent": "pythorhead/0.5",
            }
            r = REQUEST_MAP[method](full_url, headers=headers, **kwargs)
        except Exception as err:
            if not self.raise_exceptions:
                logger.error(f"Error encountered while {method} on endpoint {endpoint}: {err}")
                return
            raise err
        if not r.ok:
            if not self.raise_exceptions:
                logger.error(f"Error encountered while {method} on endpoint {endpoint}: {r.text}")
                return
            else:
                raise Exception(f"Error encountered while {method} on endpoint {endpoint}: {r.text}")

        return r.json()

    def log_in(self, username_or_email: str, password: str, totp: Optional[str] = None) -> bool:
        payload = {
            "username_or_email": username_or_email,
            "password": password,
            "totp_2fa_token": totp,
        }
        if data := self.api(Request.POST, "/user/login", json=payload):
            self._auth.set_token(data["jwt"])
        return self._auth.token is not None

    def log_out(self) -> None:
        self._auth.token = None
