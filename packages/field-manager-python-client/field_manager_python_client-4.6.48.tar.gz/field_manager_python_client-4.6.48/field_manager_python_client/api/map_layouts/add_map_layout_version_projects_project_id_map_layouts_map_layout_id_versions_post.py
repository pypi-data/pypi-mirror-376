from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.map_layout_version import MapLayoutVersion
from ...models.map_layout_version_create import MapLayoutVersionCreate
from ...types import Response


def _get_kwargs(
    project_id: str,
    map_layout_id: UUID,
    *,
    body: MapLayoutVersionCreate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/projects/{project_id}/map_layouts/{map_layout_id}/versions",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, MapLayoutVersion]]:
    if response.status_code == 201:
        response_201 = MapLayoutVersion.from_dict(response.json())

        return response_201
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[HTTPValidationError, MapLayoutVersion]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    project_id: str,
    map_layout_id: UUID,
    *,
    client: AuthenticatedClient,
    body: MapLayoutVersionCreate,
) -> Response[Union[HTTPValidationError, MapLayoutVersion]]:
    """Add Map Layout Version

     Add map layout version to map layout.

    Args:
        project_id (str):
        map_layout_id (UUID):
        body (MapLayoutVersionCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, MapLayoutVersion]]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        map_layout_id=map_layout_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    project_id: str,
    map_layout_id: UUID,
    *,
    client: AuthenticatedClient,
    body: MapLayoutVersionCreate,
) -> Optional[Union[HTTPValidationError, MapLayoutVersion]]:
    """Add Map Layout Version

     Add map layout version to map layout.

    Args:
        project_id (str):
        map_layout_id (UUID):
        body (MapLayoutVersionCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, MapLayoutVersion]
    """

    return sync_detailed(
        project_id=project_id,
        map_layout_id=map_layout_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    project_id: str,
    map_layout_id: UUID,
    *,
    client: AuthenticatedClient,
    body: MapLayoutVersionCreate,
) -> Response[Union[HTTPValidationError, MapLayoutVersion]]:
    """Add Map Layout Version

     Add map layout version to map layout.

    Args:
        project_id (str):
        map_layout_id (UUID):
        body (MapLayoutVersionCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, MapLayoutVersion]]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        map_layout_id=map_layout_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    project_id: str,
    map_layout_id: UUID,
    *,
    client: AuthenticatedClient,
    body: MapLayoutVersionCreate,
) -> Optional[Union[HTTPValidationError, MapLayoutVersion]]:
    """Add Map Layout Version

     Add map layout version to map layout.

    Args:
        project_id (str):
        map_layout_id (UUID):
        body (MapLayoutVersionCreate):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, MapLayoutVersion]
    """

    return (
        await asyncio_detailed(
            project_id=project_id,
            map_layout_id=map_layout_id,
            client=client,
            body=body,
        )
    ).parsed
