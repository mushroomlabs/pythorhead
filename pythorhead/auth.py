from typing import Optional


class Authentication:
    token: Optional[str] = None
    api_url: Optional[str] = None

    def set_token(self, token: str) -> None:
        self.token = token
