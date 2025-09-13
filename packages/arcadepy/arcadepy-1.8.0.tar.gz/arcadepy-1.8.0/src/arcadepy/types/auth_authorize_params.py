# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

from .._types import SequenceNotStr

__all__ = ["AuthAuthorizeParams", "AuthRequirement", "AuthRequirementOauth2"]


class AuthAuthorizeParams(TypedDict, total=False):
    auth_requirement: Required[AuthRequirement]

    user_id: Required[str]

    next_uri: str
    """
    Optional: if provided, the user will be redirected to this URI after
    authorization
    """


class AuthRequirementOauth2(TypedDict, total=False):
    scopes: SequenceNotStr[str]


class AuthRequirement(TypedDict, total=False):
    id: str
    """one of ID or ProviderID must be set"""

    oauth2: AuthRequirementOauth2

    provider_id: str
    """one of ID or ProviderID must be set"""

    provider_type: str
