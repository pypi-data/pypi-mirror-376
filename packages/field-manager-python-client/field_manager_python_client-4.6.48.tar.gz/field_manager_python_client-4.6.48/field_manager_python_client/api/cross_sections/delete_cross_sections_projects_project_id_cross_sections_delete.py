from http import HTTPStatus
from typing import Any, Optional, Union, cast
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response


def _get_kwargs(
    project_id: str,
    *,
    cross_section_ids: list[UUID],
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_cross_section_ids = []
    for cross_section_ids_item_data in cross_section_ids:
        cross_section_ids_item = str(cross_section_ids_item_data)
        json_cross_section_ids.append(cross_section_ids_item)

    params["cross_section_ids"] = json_cross_section_ids

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/projects/{project_id}/cross_sections",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, HTTPValidationError]]:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    project_id: str,
    *,
    client: AuthenticatedClient,
    cross_section_ids: list[UUID],
) -> Response[Union[Any, HTTPValidationError]]:
    """Delete Cross Sections

     Delete a cross section.

    Args:
        project_id (str):
        cross_section_ids (list[UUID]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        cross_section_ids=cross_section_ids,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    project_id: str,
    *,
    client: AuthenticatedClient,
    cross_section_ids: list[UUID],
) -> Optional[Union[Any, HTTPValidationError]]:
    """Delete Cross Sections

     Delete a cross section.

    Args:
        project_id (str):
        cross_section_ids (list[UUID]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return sync_detailed(
        project_id=project_id,
        client=client,
        cross_section_ids=cross_section_ids,
    ).parsed


async def asyncio_detailed(
    project_id: str,
    *,
    client: AuthenticatedClient,
    cross_section_ids: list[UUID],
) -> Response[Union[Any, HTTPValidationError]]:
    """Delete Cross Sections

     Delete a cross section.

    Args:
        project_id (str):
        cross_section_ids (list[UUID]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        cross_section_ids=cross_section_ids,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    project_id: str,
    *,
    client: AuthenticatedClient,
    cross_section_ids: list[UUID],
) -> Optional[Union[Any, HTTPValidationError]]:
    """Delete Cross Sections

     Delete a cross section.

    Args:
        project_id (str):
        cross_section_ids (list[UUID]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            project_id=project_id,
            client=client,
            cross_section_ids=cross_section_ids,
        )
    ).parsed
