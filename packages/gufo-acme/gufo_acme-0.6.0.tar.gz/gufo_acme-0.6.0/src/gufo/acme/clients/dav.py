# ---------------------------------------------------------------------
# Gufo ACME: DavAcmeClient implementation
# ---------------------------------------------------------------------
# Copyright (C) 2023-25, Gufo Labs
# ---------------------------------------------------------------------
"""A DavAcmeClient implementation."""

# Python modules
from typing import Any

# Third-party modules
from gufo.http import AuthBase, BasicAuth, Response

# Gufo ACME modules
from ..error import AcmeFulfillmentFailed
from ..types import AcmeChallenge
from .base import AcmeClient

HTTP_MAX_VALID = 299


class DavAcmeClient(AcmeClient):
    """
    WebDAV-compatible ACME Client.

    Fulfills http-01 challenge by uploading
    a token using HTTP PUT/DELETE methods
    with basic authorization.
    Works either with WebDAV modules
    or with custom scripts.

    Args:
        username: DAV user name.
        password: DAV password.
    """

    def __init__(
        self: "DavAcmeClient",
        directory_url: str,
        *,
        username: str,
        password: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(directory_url, **kwargs)
        self.username = username
        self.password = password

    def get_auth(self: "DavAcmeClient") -> AuthBase:
        """
        Get Auth for request.

        Returns:
            Auth information to be sent along with
            the request.
        """
        return BasicAuth(
            user=self.username,
            password=self.password,
        )

    @staticmethod
    def _check_dav_response(resp: Response) -> None:
        """
        Check DAV response.

        Raise an error if necessary.
        """
        if resp.status > HTTP_MAX_VALID:
            msg = f"Failed to put challenge: code {resp.status}"
            raise AcmeFulfillmentFailed(msg)

    async def fulfill_http_01(
        self: "DavAcmeClient", domain: str, challenge: AcmeChallenge
    ) -> bool:
        """
        Perform http-01 fullfilment.

        Execute PUT method to place a token.

        Args:
            domain: Domain name
            challenge: AcmeChallenge instance, containing token.

        Returns:
            True - on succeess

        Raises:
            AcmeFulfillmentFailed: On error.
        """
        async with self._get_client(auth=self.get_auth()) as client:
            v = self.get_key_authorization(challenge)
            resp = await client.put(
                f"http://{domain}/.well-known/acme-challenge/{challenge.token}",
                v,
            )
            self._check_dav_response(resp)
        return True

    async def clear_http_01(
        self: "DavAcmeClient", domain: str, challenge: AcmeChallenge
    ) -> None:
        """
        Remove provisioned token.

        Args:
            domain: Domain name
            challenge: AcmeChallenge instance, containing token.

        Raises:
            AcmeFulfillmentFailed: On error.
        """
        async with self._get_client(auth=self.get_auth()) as client:
            resp = await client.delete(
                f"http://{domain}/.well-known/acme-challenge/{challenge.token}",
            )
            self._check_dav_response(resp)
