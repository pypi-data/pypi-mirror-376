import os
from typing import Annotated, Optional, List
from pydantic import Field
from mcp.server.fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_sheets_mcpserver.model import *

mcp = FastMCP("netmind-mcpserver-mcp")

creds = Credentials(
    token=os.environ["GOOGLE_ACCESS_TOKEN"],
    refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive.metadata"
    ]
)
service = build("sheets", "v4", credentials=creds)


@mcp.tool(description="Creates a spreadsheet")
async def create_spreadsheet(
    properties: Annotated[SpreadsheetProperties, Field(description="Properties of the spreadsheet")],
    sheets: Annotated[Optional[List[Sheets]], Field(description="List of sheets in the spreadsheet")] = None,
):
    spreadsheet_body = {
        "properties": properties.model_dump(mode="json"),
        "sheets": [sheet.model_dump(mode="json") for sheet in sheets] if sheets else [],
    }
    created = service.spreadsheets().create(body=spreadsheet_body).execute()
    return created


@mcp.tool(description="Gets a spreadsheet by ID")
async def get_spreadsheet(
    spreadsheetId: Annotated[str, Field(description="The ID of the spreadsheet to retrieve")],
    ranges: Annotated[Optional[List[str]], Field(description="The ranges to retrieve from the spreadsheet")] = None,
    includeGridData: Annotated[Optional[bool], Field(description="Whether to include grid data")] = False,
    excludeTablesInBandedRanges: Annotated[Optional[bool], Field(description="Whether to exclude tables in banded ranges")] = False,
):
    response = service.spreadsheets().get(
        spreadsheetId=spreadsheetId,
        ranges=ranges,
        includeGridData=includeGridData,
        excludeTablesInBandedRanges=excludeTablesInBandedRanges,
    ).execute()
    return response


@mcp.tool(description="Lists the user's spreadsheets")
async def list_spreadsheets(
    pageSize: Annotated[Optional[int], Field(description="The maximum number of files to return")] = 10,
    pageToken: Annotated[Optional[str], Field(description="The token for continuing a previous list request")] = None,
    query: Annotated[Optional[str], Field(description="Optional filter for spreadsheets (e.g., \"name contains 'report'\")")] = None,
):
    default_query = "mimeType='application/vnd.google-apps.spreadsheet'"
    if query:
        query = f"({default_query}) and ({query})"

    drive_service = build("drive", "v3", credentials=creds)
    fields = "nextPageToken, files(id, name, mimeType, modifiedTime)"
    response = drive_service.files().list(
        pageSize=pageSize,
        pageToken=pageToken,
        q=query,
        fields=fields,
    ).execute()
    return response


@mcp.tool(description="Retrieve a spreadsheet or specific ranges using data filters, with optional grid data.")
async def get_filtered_spreadsheet(
    spreadsheetId: Annotated[str, Field(description="The ID of the spreadsheet to retrieve")],
    dataFilters: Annotated[List[DataFilters], Field(description="The data filters to apply")],
    includeGridData: Annotated[Optional[bool], Field(description="Whether to include grid data")] = False,
    excludeTablesInBandedRanges: Annotated[Optional[bool], Field(description="Whether to exclude tables in banded ranges")] = False,
):
    body = {
        "dataFilters": [dataFilter.model_dump(mode="json") for dataFilter in dataFilters],
        "includeGridData": includeGridData,
        "excludeTablesInBandedRanges": excludeTablesInBandedRanges,
    }
    response = service.spreadsheets().getByDataFilter(
        spreadsheetId=spreadsheetId, body=body
    ).execute()
    return response


@mcp.tool(description="Applies batch updates to a spreadsheet")
async def batch_update_spreadsheet(
    spreadsheetId: Annotated[str, Field(description="The ID of the spreadsheet to update")],
    requests: Annotated[List[Request], Field(description="The list of update requests to apply")],
    responseRanges: Annotated[Optional[List[str]], Field(description="The ranges to include in the response")] = None,
    includeSpreadsheetInResponse: Annotated[Optional[bool], Field(description="Whether to include the updated spreadsheet in the response")] = False,
    responseIncludeGridData: Annotated[Optional[bool], Field(description="Whether to include grid data in the response")] = False,
):
    body = {
        "requests": [request.model_dump(mode="json") for request in requests],
        "includeSpreadsheetInResponse": includeSpreadsheetInResponse,
        "responseRanges": responseRanges if responseRanges else [],
        "responseIncludeGridData": responseIncludeGridData,
    }
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheetId, body=body
    ).execute()
    return response


@mcp.tool(description="Copies a sheet to another spreadsheet")
async def copy_sheet_to(
    spreadsheetId: Annotated[str, Field(description="The ID of the source spreadsheet")],
    sheetId: Annotated[int, Field(description="The ID of the sheet to copy")],
    destinationSpreadsheetId: Annotated[str, Field(description="The ID of the destination spreadsheet")]
):
    response = service.spreadsheets().sheets().copyTo(
        spreadsheetId=spreadsheetId,
        sheetId=sheetId,
        body={"destinationSpreadsheetId": destinationSpreadsheetId}
    ).execute()
    return response


@mcp.tool(description="Appends values to a spreadsheet")
async def append_values(
    spreadsheetId: Annotated[str, Field(description="The ID of the spreadsheet to update")],
    range: Annotated[str, Field(description="The A1 notation of the range to append values to")],
    body: Annotated[ValueRange, Field(description="The values to append")],
    valueInputOption: Annotated[Optional[ValueInputOption], Field(description="How the input data should be interpreted")] = None,
    insertDataOption: Annotated[Optional[InsertDataOption], Field(description="How the input data should be inserted")] = None,
):
    body = body.model_dump(mode="json")
    response = service.spreadsheets().values().append(
        spreadsheetId=spreadsheetId,
        range=range,
        valueInputOption=valueInputOption.value if valueInputOption else None,
        insertDataOption=insertDataOption.value if insertDataOption else None,
        body=body
    ).execute()
    return response


@mcp.tool(description="Gets values from a spreadsheet")
async def get_values(
    spreadsheetId: Annotated[str, Field(description="The ID of the spreadsheet to retrieve values from")],
    range: Annotated[str, Field(description="The A1 notation of the range to retrieve values from")],
    majorDimension: Annotated[Optional[Dimension], Field(description="The major dimension of the values")] = Dimension.ROWS,
    valueRenderOption: Annotated[Optional[ValueRenderOption], Field(description="How values should be rendered")] = ValueRenderOption.FORMATTED_VALUE,
    dateTimeRenderOption: Annotated[Optional[DateTimeRenderOption], Field(description="How dates, times, and durations should be rendered")] = DateTimeRenderOption.SERIAL_NUMBER
):
    response = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId,
        range=range,
        majorDimension=majorDimension.value if majorDimension else None,
        valueRenderOption=valueRenderOption.value if valueRenderOption else None,
        dateTimeRenderOption=dateTimeRenderOption.value if dateTimeRenderOption else None
    ).execute()
    return response


@mcp.tool(description="Updates values in a spreadsheet")
async def update_values(
    spreadsheetId: Annotated[str, Field(description="The ID of the spreadsheet to update values in")],
    range: Annotated[str, Field(description="The A1 notation of the range to update values in")],
    body: Annotated[ValueRange, Field(description="The values to update")],
    valueInputOption: Annotated[Optional[ValueInputOption], Field(description="How the input data should be interpreted")] = None,
    includeValuesInResponse: Annotated[Optional[bool], Field(description="Whether to include the updated values in the response")] = False,
    responseValueRenderOption: Annotated[Optional[ValueRenderOption], Field(description="How values should be rendered in the response")] = ValueRenderOption.FORMATTED_VALUE,
    responseDateTimeRenderOption: Annotated[Optional[DateTimeRenderOption], Field(description="How dates, times, and durations should be rendered in the response")] = DateTimeRenderOption.SERIAL_NUMBER
):
    body = body.model_dump(mode="json")
    response = service.spreadsheets().values().update(
        spreadsheetId=spreadsheetId,
        range=range,
        body=body,
        valueInputOption=valueInputOption.value if valueInputOption else None,
        includeValuesInResponse=includeValuesInResponse,
        responseValueRenderOption=responseValueRenderOption.value if responseValueRenderOption else None,
        responseDateTimeRenderOption=responseDateTimeRenderOption.value if responseDateTimeRenderOption else None
    ).execute()
    return response


@mcp.tool(description="Clears values from a spreadsheet")
async def clear_values(
    spreadsheetId: Annotated[str, Field(description="The ID of the spreadsheet to clear values from")],
    range: Annotated[str, Field(description="The A1 notation of the range to clear values from")]
):
    response = service.spreadsheets().values().clear(
        spreadsheetId=spreadsheetId,
        range=range,
        body={}
    ).execute()
    return response


@mcp.tool(description="Gets values from a spreadsheet using batch get")
async def batch_get_values(
    spreadsheetId: Annotated[str, Field(description="The ID of the spreadsheet to retrieve values from")],
    ranges: Annotated[List[str], Field(description="The A1 notation of the ranges to retrieve values from")],
    majorDimension: Annotated[Optional[Dimension], Field(description="The major dimension of the values")] = Dimension.ROWS,
    valueRenderOption: Annotated[Optional[ValueRenderOption], Field(description="How values should be rendered")] = ValueRenderOption.FORMATTED_VALUE,
    dateTimeRenderOption: Annotated[Optional[DateTimeRenderOption], Field(description="How dates, times, and durations should be rendered")] = DateTimeRenderOption.SERIAL_NUMBER
):
    response = service.spreadsheets().values().batchGet(
        spreadsheetId=spreadsheetId,
        ranges=ranges,
        majorDimension=majorDimension.value if majorDimension else None,
        valueRenderOption=valueRenderOption.value if valueRenderOption else None,
        dateTimeRenderOption=dateTimeRenderOption.value if dateTimeRenderOption else None
    ).execute()
    return response


@mcp.tool(description="Updates values in a spreadsheet using batch update")
async def batch_update_values(
    spreadsheetId: Annotated[str, Field(description="The ID of the spreadsheet to update values in")],
    data: Annotated[List[ValueRange], Field(description="The list of value ranges to update")],
    valueInputOption: Annotated[Optional[ValueInputOption], Field(description="How the input data should be interpreted")] = None,
    includeValuesInResponse: Annotated[Optional[bool], Field(description="Whether to include the updated values in the response")] = False,
    responseValueRenderOption: Annotated[Optional[ValueRenderOption], Field(description="How values should be rendered in the response")] = ValueRenderOption.FORMATTED_VALUE,
    responseDateTimeRenderOption: Annotated[Optional[DateTimeRenderOption], Field(description="How dates, times, and durations should be rendered in the response")] = DateTimeRenderOption.SERIAL_NUMBER
):
    body = {
        "valueInputOption": valueInputOption.value if valueInputOption else None,
        "data": [item.model_dump(mode="json") for item in data],
        "includeValuesInResponse": includeValuesInResponse,
        "responseValueRenderOption": responseValueRenderOption.value if responseValueRenderOption else None,
        "responseDateTimeRenderOption": responseDateTimeRenderOption.value if responseDateTimeRenderOption else None
    }
    response = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheetId,
        body=body
    ).execute()
    return response


@mcp.tool(description="Clears values from a spreadsheet using batch clear")
async def batch_clear_values(
    spreadsheetId: Annotated[str, Field(description="The ID of the spreadsheet to clear values from")],
    ranges: Annotated[List[str], Field(description="The A1 notation of the ranges to clear values from")]
):
    body = {"ranges": ranges}
    response = service.spreadsheets().values().batchClear(
        spreadsheetId=spreadsheetId,
        body=body
    ).execute()
    return response


@mcp.tool(description="Gets values from a spreadsheet using batch get by data filter")
async def batch_get_values_by_data_filter(
    spreadsheetId: Annotated[str, Field(description="The ID of the spreadsheet to retrieve values from")],
    dataFilters: Annotated[List[DataFilters], Field(description="The data filters to apply")],
    majorDimension: Annotated[Optional[Dimension], Field(description="The major dimension of the values")] = Dimension.ROWS,
    valueRenderOption: Annotated[Optional[ValueRenderOption], Field(description="How values should be rendered")] = ValueRenderOption.FORMATTED_VALUE,
    dateTimeRenderOption: Annotated[Optional[DateTimeRenderOption], Field(description="How dates, times, and durations should be rendered")] = DateTimeRenderOption.SERIAL_NUMBER
):
    body = {
        "dataFilters": [dataFilter.model_dump(mode="json") for dataFilter in dataFilters],
        "majorDimension": majorDimension.value if majorDimension else None,
        "valueRenderOption": valueRenderOption.value if valueRenderOption else None,
        "dateTimeRenderOption": dateTimeRenderOption.value if dateTimeRenderOption else None
    }
    response = service.spreadsheets().values().batchGetByDataFilter(
        spreadsheetId=spreadsheetId,
        body=body
    ).execute()
    return response


@mcp.tool(description="Updates values in a spreadsheet using batch update by data filter")
async def batch_update_values_by_data_filter(
    spreadsheetId: Annotated[str, Field(description="The ID of the spreadsheet to update values in")],
    data: Annotated[List[DataFilterValueRange], Field(description="The list of data filter value ranges to update")],
    valueInputOption: Annotated[Optional[ValueInputOption], Field(description="How the input data should be interpreted")] = None,
    includeValuesInResponse: Annotated[Optional[bool], Field(description="Whether to include the updated values in the response")] = False,
    responseValueRenderOption: Annotated[Optional[ValueRenderOption], Field(description="How values should be rendered in the response")] = ValueRenderOption.FORMATTED_VALUE,
    responseDateTimeRenderOption: Annotated[Optional[DateTimeRenderOption], Field(description="How dates, times, and durations should be rendered in the response")] = DateTimeRenderOption.SERIAL_NUMBER
):
    body = {
        "valueInputOption": valueInputOption.value if valueInputOption else None,
        "data": [item.model_dump(mode="json") for item in data],
        "includeValuesInResponse": includeValuesInResponse,
        "responseValueRenderOption": responseValueRenderOption.value if responseValueRenderOption else None,
        "responseDateTimeRenderOption": responseDateTimeRenderOption.value if responseDateTimeRenderOption else None
    }
    response = service.spreadsheets().values().batchUpdateByDataFilter(
        spreadsheetId=spreadsheetId,
        body=body
    ).execute()
    return response


@mcp.tool(description="Clears values from a spreadsheet using batch clear by data filter")
async def batch_clear_values_by_data_filter(
    spreadsheetId: Annotated[str, Field(description="The ID of the spreadsheet to clear values from")],
    dataFilters: Annotated[List[DataFilters], Field(description="The data filters to apply")]
):
    body = {
        "dataFilters": [dataFilter.model_dump(mode="json") for dataFilter in dataFilters]
    }
    response = service.spreadsheets().values().batchClearByDataFilter(
        spreadsheetId=spreadsheetId,
        body=body
    ).execute()
    return response


def main():
    mcp.run()


if __name__ == '__main__':
    main()
