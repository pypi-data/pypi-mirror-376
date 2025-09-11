from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.export import Export
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    project_id: str,
    *,
    body: Export,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/projects/{project_id}/export",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = response.json()
        return response_200
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
    body: Export,
) -> Response[Union[Any, HTTPValidationError]]:
    """Export

     Endpoint for exporting project data.

    Supported **export_type**:

    - **LocationCSV**: Download CSV file with key location information (onshore format).
    - **LocationGeoJSON**: Download GeoJSON files.
    - **LocationKOF**: Download KOF files.
    - **LocationLAS**: Download LAS files.
    - **LocationXLS**: Download Excel file with key location information (onshore format).
    - **MethodFiles**: Download all original uploaded source data files.
    - **MethodSND**: Download SND files for all methods in a Zip file.
    - **MethodXLS**: Download Excel file with method data (offshore format).
    - **ProjectFiles**: Download files, with ID listed in the file_ids, in a Zip file.

    **method_status_ids**: Filter methods by status. Only return specified statuses. Empty list means
    all statuses.

    **method_type_ids**: Filter methods by type. Only return specified method types. Empty list means
    all types.

    **method_conducted_from**: Optional filter. Only return methods conducted after this time.

    **method_conducted_to**: Optional filter. Only return methods conducted before (this time + one
    day).

    Args:
        project_id (str):
        body (Export):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    project_id: str,
    *,
    client: AuthenticatedClient,
    body: Export,
) -> Optional[Union[Any, HTTPValidationError]]:
    """Export

     Endpoint for exporting project data.

    Supported **export_type**:

    - **LocationCSV**: Download CSV file with key location information (onshore format).
    - **LocationGeoJSON**: Download GeoJSON files.
    - **LocationKOF**: Download KOF files.
    - **LocationLAS**: Download LAS files.
    - **LocationXLS**: Download Excel file with key location information (onshore format).
    - **MethodFiles**: Download all original uploaded source data files.
    - **MethodSND**: Download SND files for all methods in a Zip file.
    - **MethodXLS**: Download Excel file with method data (offshore format).
    - **ProjectFiles**: Download files, with ID listed in the file_ids, in a Zip file.

    **method_status_ids**: Filter methods by status. Only return specified statuses. Empty list means
    all statuses.

    **method_type_ids**: Filter methods by type. Only return specified method types. Empty list means
    all types.

    **method_conducted_from**: Optional filter. Only return methods conducted after this time.

    **method_conducted_to**: Optional filter. Only return methods conducted before (this time + one
    day).

    Args:
        project_id (str):
        body (Export):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return sync_detailed(
        project_id=project_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    project_id: str,
    *,
    client: AuthenticatedClient,
    body: Export,
) -> Response[Union[Any, HTTPValidationError]]:
    """Export

     Endpoint for exporting project data.

    Supported **export_type**:

    - **LocationCSV**: Download CSV file with key location information (onshore format).
    - **LocationGeoJSON**: Download GeoJSON files.
    - **LocationKOF**: Download KOF files.
    - **LocationLAS**: Download LAS files.
    - **LocationXLS**: Download Excel file with key location information (onshore format).
    - **MethodFiles**: Download all original uploaded source data files.
    - **MethodSND**: Download SND files for all methods in a Zip file.
    - **MethodXLS**: Download Excel file with method data (offshore format).
    - **ProjectFiles**: Download files, with ID listed in the file_ids, in a Zip file.

    **method_status_ids**: Filter methods by status. Only return specified statuses. Empty list means
    all statuses.

    **method_type_ids**: Filter methods by type. Only return specified method types. Empty list means
    all types.

    **method_conducted_from**: Optional filter. Only return methods conducted after this time.

    **method_conducted_to**: Optional filter. Only return methods conducted before (this time + one
    day).

    Args:
        project_id (str):
        body (Export):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    project_id: str,
    *,
    client: AuthenticatedClient,
    body: Export,
) -> Optional[Union[Any, HTTPValidationError]]:
    """Export

     Endpoint for exporting project data.

    Supported **export_type**:

    - **LocationCSV**: Download CSV file with key location information (onshore format).
    - **LocationGeoJSON**: Download GeoJSON files.
    - **LocationKOF**: Download KOF files.
    - **LocationLAS**: Download LAS files.
    - **LocationXLS**: Download Excel file with key location information (onshore format).
    - **MethodFiles**: Download all original uploaded source data files.
    - **MethodSND**: Download SND files for all methods in a Zip file.
    - **MethodXLS**: Download Excel file with method data (offshore format).
    - **ProjectFiles**: Download files, with ID listed in the file_ids, in a Zip file.

    **method_status_ids**: Filter methods by status. Only return specified statuses. Empty list means
    all statuses.

    **method_type_ids**: Filter methods by type. Only return specified method types. Empty list means
    all types.

    **method_conducted_from**: Optional filter. Only return methods conducted after this time.

    **method_conducted_to**: Optional filter. Only return methods conducted before (this time + one
    day).

    Args:
        project_id (str):
        body (Export):

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
            body=body,
        )
    ).parsed
