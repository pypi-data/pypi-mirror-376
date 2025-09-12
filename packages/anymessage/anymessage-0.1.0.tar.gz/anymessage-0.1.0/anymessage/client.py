import aiohttp
from typing import Optional, Any, Dict, Union

BASE_URL = "https://api.anymessage.shop"


class AnyMessageClient:
    """
    Asynchronous SDK for AnyMessage API.

    Initialization:
    client = AnyMessageClient(token="token")

    Methods:
        - get_balance() -> Dict[str, Any]
        - get_email_quantity(site: str) -> Dict[str, Any]
        - order_email(site: str, domain: str, regex: Optional[str] = None, subject: Optional[str] = None) -> Dict[str, Any]
        - get_message(id: str, preview: bool) -> Union[Dict[str, Any], str]
        - reorder_email(id: Optional[str] = None, email: Optional[str] = None, site: Optional[str] = None) -> Dict[str, Any]
        - cancel_email(id: str) -> Dict[str, Any]
    """

    def __init__(self, token: str):
        """
        :param token: Your API Token for AnyMessage.
        """
        self.token = token
        self.base_url = BASE_URL
        self.session = None

    async def __aenter__(self):
        """Initialize aiohttp session."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()

    async def _make_request(
        self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], str]:
        """
        Internal method to make HTTP request.
        Handles errors and returns response.

        :param method:
        :param endpoint:
        :param params:
        :return:
        """
        if not self.session:
            raise RuntimeError(
                'Session not initialized. Use "async with AnyMessageClient()".'
            )

        url = f"{self.base_url}/{endpoint}"
        request_params = {"token": self.token}
        if params:
            request_params.update(params)

        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with self.session.request(
                method, url, params=request_params, timeout=timeout
            ) as response:
                response.raise_for_status()
                content = await response.text()
                content = content.strip()
                if content.startswith("<!DOCTYPE html>"):  # For preview=1
                    return content
                return await response.json()
        except aiohttp.ClientError as e:
            raise ValueError(f"API request failed: {e}")

    async def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance.
        :return: {"status": "success", "balance": "1.0"}
        """
        return await self._make_request("GET", "user/balance")

    async def get_email_quantity(self, site: str) -> Dict[str, Any]:
        """
        Get Available email quantity for a site.
        :param site: Site, e.g., "instagram.com"
        :return: {"status": "success", "data": {...}}
        """
        params = {"site": site}
        return await self._make_request("GET", "email/quantity", params=params)

    async def order_email(
        self,
        site: str,
        domain: str,
        regex: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Order an email.
        :param site: Site, e.g., "instagram.com"
        :param domain: Domain(s), e.g., "gmx" or "mailcom,gmx,hotmail")
        :param regex: Optional regex.
        :param subject: Optional subject.
        :return: {"status": "success", "id": "1001", "email": "test@gmx.com"}
        """
        params = {"site": site, "domain": domain}
        if regex:
            params["regex"] = regex
        if subject:
            params["subject"] = subject
        return await self._make_request("GET", "email/order", params=params)

    async def get_message(
        self, id: str, preview: bool = False
    ) -> Union[Dict[str, Any], str]:
        """
        Get message by ID.
        :param id: Activation ID (email ord)
        :param preview: If True, returns raw HTML, else JSON with HTML in 'message'
        :return: JSON or HTML
        """
        params = {"id": id}
        if preview:
            params["preview"] = "1"
        return await self._make_request("GET", "email/getmessage", params=params)

    async def reorder_email(
        self,
        id: Optional[str] = None,
        email: Optional[str] = None,
        site: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reorder email.
        Use either id or (email+site).
        :param id: ID for reordering
        :param email: Email for reordering
        :param site: Site for email
        :return: {"status": "success", "id": "1001", "email": "test@gmx.com"}
        """
        if id:
            params = {"id": id}
        elif email and site:
            params = {"email": email, "site": site}
        else:
            raise ValueError("Provide either 'id' or 'email' + 'site'")
        return await self._make_request("GET", "email/reorder", params=params)

    async def cancel_email(self, id: str) -> Dict[str, Any]:
        """
        Cancel email.
        :param id: Activation ID
        :return: {"status": "success", "value": "activation canceled"}
        """
        params = {"id": id}
        return await self._make_request("GET", "email/cancel", params=params)
