import logging
from typing import Optional

from pythorhead.requestor import Request, Requestor, REQUEST_MAP

logger = logging.getLogger(__name__)


class Image:
    def __init__(self, _requestor: Requestor) -> None:
        self._requestor = _requestor

    @property
    def pictrs_base_url(self):
        return f"{self._requestor.instance_url}/pictrs"

    @property
    def auth_token(self):
        return self._requestor._auth.token

    def _make_request(self, method, endpoint, **kwargs) -> Optional[dict]:
        logger.info(f"Requesting image {method} on {endpoint}")
        try:
            full_url = f"{self.pictrs_base_url}/{endpoint}"
            cookies = {"jwt": self.auth_token}
            r = REQUEST_MAP[method](full_url, cookies=cookies, **kwargs)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            if self._requestor.raise_exceptions:
                raise exc
            else:
                logger.error(f"Error encountered while {method} on {full_url}: {exc}")
                return None

    def upload(self, image_path: str) -> Optional[dict]:
        """

        Upload an image synchronously (waits for validation and get the data)

        Args:
            image_path (str)

        Returns:
            Optional[dict]: image data if successful
        """

        with open(image_path, "rb") as image:
            data = self._make_request(Request.POST, "image", files={"images[]": image})

            if data and "files" in data:
                for file in data["files"]:
                    file["image_url"] = "/".join(
                        (
                            self.pictrs_base_url,
                            "image",
                            file["file"],
                        ),
                    )
                    file["delete_url"] = "/".join(
                        (
                            self.pictrs_base_url,
                            "image",
                            "delete",
                            file["delete_token"],
                            file["file"],
                        ),
                    )
                    del file["file"]
                    del file["delete_token"]

                return data["files"]

    def async_upload(self, image_path: str) -> str:
        """

        Upload an image

        Args:
            image_path (str)

        Returns:
            str: UUID representing the task id
        """

        with open(image_path, "rb") as image:
            data = self._make_request(Request.POST, "image/backgrounded", files={"images[]": image})

            assert data is not None, "request failed"
            assert "uploads" in data, "information about upload_id not present"
            assert len(data["uploads"]) == 1, "We should get only one uploaded item"
            return data["uploads"][0]["upload_id"]
