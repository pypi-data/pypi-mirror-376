from typing import List, Optional, Annotated
from pydantic import Field
from pydantic import BaseModel
from enum import Enum


class SpreadsheetProperties(BaseModel):
    title: str = Field(description="Title of the spreadsheet")
    locale: Optional[str] = Field(default=None, description="Locale of the spreadsheet, e.g., 'en_US'")
    timeZone: Optional[str] = Field(default=None, description="Time zone of the spreadsheet, e.g., 'America/New_York'")


class SheetType(str, Enum):
    SHEET_TYPE_UNSPECIFIED = "SHEET_TYPE_UNSPECIFIED"
    GRID = "GRID"
    OBJECT = "OBJECT"
    DATA_SOURCE = "DATA_SOURCE"


class GridProperties(BaseModel):
    rowCount: Optional[int] = Field(default=None, description="Number of rows in the grid")
    columnCount: Optional[int] = Field(default=None, description="Number of columns in the grid")
    frozenRowCount: Optional[int] = Field(default=None, description="Number of frozen rows")
    frozenColumnCount: Optional[int] = Field(default=None, description="Number of frozen columns")
    hideGridlines: Optional[bool] = Field(default=False, description="Whether gridlines are hidden")
    rowGroupControlAfter: Optional[bool] = Field(default=False,
                                                 description="Whether row group control is after the row")
    columnGroupControlAfter: Optional[bool] = Field(default=False,
                                                    description="Whether column group control is after the column")


class GridRange(BaseModel):
    sheetId: Optional[int] = Field(default=None, description="Unique identifier for the sheet")
    startRowIndex: Optional[int] = Field(default=None, description="Starting row index (0-based, inclusive)")
    endRowIndex: Optional[int] = Field(default=None, description="Ending row index (0-based, exclusive)")
    startColumnIndex: Optional[int] = Field(default=None, description="Starting column index (0-based, inclusive)")
    endColumnIndex: Optional[int] = Field(default=None, description="Ending column index (0-based, exclusive)")


class SheetProperties(BaseModel):
    sheetId: Optional[int] = Field(default=None, description="Unique identifier for the sheet")
    title: str = Field(description="Title of the sheet")
    index: Optional[int] = Field(default=None, description="Index of the sheet in the spreadsheet")
    sheetType: Optional[SheetType] = Field(default=SheetType.GRID, description="Type of the sheet")
    hidden: Optional[bool] = Field(default=False, description="Whether the sheet is hidden")
    tabColorStyle: Optional[dict] = Field(default=None, description="Color style of the sheet tab")
    rightToLeft: Optional[bool] = Field(default=False, description="Whether the sheet is right-to-left")


class CellData(BaseModel):
    userEnteredValue: Optional[dict] = Field(default=None, description="The value entered by the user")
    effectiveValue: Optional[dict] = Field(default=None, description="The effective value of the cell")
    # formattedValue: Optional[str] = Field(default=None, description="The formatted value of the cell")
    userEnteredFormat: Optional[dict] = Field(default=None, description="The format set by the user")
    effectiveFormat: Optional[dict] = Field(default=None, description="The effective format of the cell")
    hyperlink: Optional[str] = Field(default=None, description="Hyperlink in the cell")
    note: Optional[str] = Field(default=None, description="Note attached to the cell")


class RowData(BaseModel):
    values: Optional[List[CellData]] = Field(default=None, description="List of cell data in the row")


class DimensionProperties(BaseModel):
    hiddenByFilter: Optional[bool] = Field(default=False, description="Whether the dimension is hidden by a filter")
    hiddenByUser: Optional[bool] = Field(default=False, description="Whether the dimension is hidden by the user")
    pixelSize: Optional[int] = Field(default=None, description="Size of the dimension in pixels")


class GridData(BaseModel):
    startRow: Optional[int] = Field(default=None, description="Starting row index of the grid data")
    startColumn: Optional[int] = Field(default=None, description="Starting column index of the grid data")
    rowData: Optional[List[RowData]] = Field(default=None, description="List of row data")
    rowMetadata: Optional[List[DimensionProperties]] = Field(default=None, description="Metadata for rows")
    columnMetadata: Optional[List[DimensionProperties]] = Field(default=None, description="Metadata for columns")


class Table(BaseModel):
    tableId: Optional[str] = Field(default=None, description="Unique identifier for the table")
    name: Optional[str] = Field(default=None, description="Name of the table")
    range: Optional[GridRange] = Field(default=None, description="Range of the table in the sheet")
    rowsProperties: Optional[dict] = Field(default=None, description="Properties of the rows in the table")
    columnProperties: Optional[List[dict]] = Field(default=None, description="Properties of the columns in the table")


class Sheets(BaseModel):
    properties: SheetProperties = Field(description="Properties of the sheet")
    data: Optional[List[GridData]] = Field(default=None, description="Grid data of the sheet")
    tables: Optional[List[Table]] = Field(default=None, description="Tables in the sheet")


class Spreadsheets(BaseModel):
    properties: SpreadsheetProperties = Field(description="Properties of the spreadsheet")
    sheets: List[Sheets] = Field(description="List of sheets in the spreadsheet")


class DataFilters(BaseModel):
    a1range: str = Field(description="The A1 notation of the range to filter")
    gridRange: GridRange = Field(description="The grid range to filter")


class ValueInputOption(str, Enum):
    INPUT_VALUE_OPTION_UNSPECIFIED = "INPUT_VALUE_OPTION_UNSPECIFIED"
    RAW = "RAW"
    USER_ENTERED = "USER_ENTERED"


class InsertDataOption(str, Enum):
    OVERWRITE = "OVERWRITE"
    INSERT_ROWS = "INSERT_ROWS"


class Dimension(str, Enum):
    DIMENSION_UNSPECIFIED = "DIMENSION_UNSPECIFIED"
    ROWS = "ROWS"
    COLUMNS = "COLUMNS"


class ValueRange(BaseModel):
    range: Optional[str] = Field(default=None, description="The A1 notation of the values' range")
    majorDimension: Optional[Dimension] = Field(default=Dimension.ROWS, description="The major dimension of the values")
    values: List[List] = Field(description="The values to be written")


class ValueRenderOption(str, Enum):
    FORMATTED_VALUE = "FORMATTED_VALUE"
    UNFORMATTED_VALUE = "UNFORMATTED_VALUE"
    FORMULA = "FORMULA"


class DateTimeRenderOption(str, Enum):
    SERIAL_NUMBER = "SERIAL_NUMBER"
    FORMATTED_STRING = "FORMATTED_STRING"


class DataFilterValueRange(BaseModel):
    dataFilter: DataFilters = Field(description="The data filter to apply")
    majorDimension: Optional[Dimension] = Field(default=Dimension.ROWS, description="The major dimension of the values")
    values: List[List] = Field(description="The values to be written")


class UpdateSpreadsheetPropertiesRequest(BaseModel):
    properties: SpreadsheetProperties = Field(description="Properties to update")
    fields: str = Field(description="Comma-separated list of fields to update, e.g., 'title,locale,timeZone'")


class UpdateSheetPropertiesRequest(BaseModel):
    properties: SheetProperties = Field(description="Properties to update")
    fields: str = Field(description="Comma-separated list of fields to update, e.g., 'title,index,hidden'")


class AddSheetRequest(BaseModel):
    properties: SheetProperties = Field(description="Properties of the new sheet")


class DeleteSheetRequest(BaseModel):
    sheetId: int = Field(description="Unique identifier of the sheet to delete")


class DuplicateSheetRequest(BaseModel):
    sourceSheetId: int = Field(description="Unique identifier of the sheet to duplicate")
    insertSheetIndex: Optional[int] = Field(default=None, description="Index to insert the duplicated sheet at")
    newSheetId: Optional[int] = Field(default=None, description="Unique identifier for the new duplicated sheet")
    newSheetName: Optional[str] = Field(default=None, description="Name of the new duplicated sheet")


class AddTableRequest(BaseModel):
    table: Table = Field(description="Properties of the new table")


class UpdateTableRequest(BaseModel):
    table: Table = Field(description="Properties to update")
    fields: str = Field(description="Comma-separated list of fields to update, e.g., 'name,range'")


class DeleteTableRequest(BaseModel):
    tableId: str = Field(description="Unique identifier of the table to delete")


class DimensionRange(BaseModel):
    sheetId: int = Field(description="Unique identifier of the sheet")
    dimension: Dimension = Field(description="The dimension to operate on (ROWS or COLUMNS)")
    startIndex: int = Field(description="Starting index (0-based, inclusive)")
    endIndex: int = Field(description="Ending index (0-based, exclusive)")


class InsertDimensionRequest(BaseModel):
    range: DimensionRange = Field(description="The range of dimensions to insert")
    inheritFromBefore: Optional[bool] = Field(default=False, description="Whether to inherit properties from the dimension before")


class DeleteDimensionRequest(BaseModel):
    range: DimensionRange = Field(description="The range of dimensions to delete")


class FindReplaceRequest(BaseModel):
    find: str = Field(description="The text to find")
    replacement: str = Field(description="The text to replace with")
    matchCase: Optional[bool] = Field(default=False, description="Whether to match case")
    matchEntireCell: Optional[bool] = Field(default=False, description="Whether to match entire cell contents")
    searchByRegex: Optional[bool] = Field(default=False, description="Whether to interpret 'find' as a regex")
    includeFormulas: Optional[bool] = Field(default=False, description="Whether to include formulas in the search")
    range: Optional[GridRange] = Field(default=None, description="The range to search within")
    allSheets: Optional[bool] = Field(default=False, description="Whether to search all sheets")
    sheetId: Optional[int] = Field(default=None, description="Unique identifier of the sheet to search in")


class InsertRangeRequest(BaseModel):
    range: GridRange = Field(description="The range to insert cells into")
    shiftDimension: Dimension = Field(description="The dimension to shift (ROWS or COLUMNS)")


class MergeType(str, Enum):
    MERGE_ALL = "MERGE_ALL"
    MERGE_COLUMNS = "MERGE_COLUMNS"
    MERGE_ROWS = "MERGE_ROWS"


class MergeCellsRequest(BaseModel):
    range: GridRange = Field(description="The range of cells to merge")
    mergeType: MergeType = Field(description="The type of merge to perform")


class UnmergeCellsRequest(BaseModel):
    range: GridRange = Field(description="The range of cells to unmerge")

class GridCoordinates(BaseModel):
    sheetId: int = Field(description="Unique identifier for the sheet")
    rowIndex: int = Field(description="Row index (0-based)")
    columnIndex: int = Field(description="Column index (0-based)")


class PasteType(str, Enum):
    PASTE_NORMAL = "PASTE_NORMAL"
    PASTE_VALUES = "PASTE_VALUES"
    PASTE_FORMAT = "PASTE_FORMAT"
    PASTE_NO_BORDERS = "PASTE_NO_BORDERS"
    PASTE_FORMULA = "PASTE_FORMULA"
    PASTE_DATA_VALIDATION = "PASTE_DATA_VALIDATION"
    PASTE_CONDITIONAL_FORMATTING = "PASTE_CONDITIONAL_FORMATTING"


class CutPasteRequest(BaseModel):
    source: GridRange = Field(description="The source range to cut")
    destination: GridCoordinates = Field(description="The top-left corner of the destination range")
    pasteType: Optional[PasteType] = Field(default=PasteType.PASTE_NORMAL, description="The type of paste to perform")


class PasteOrientation(str, Enum):
    NORMAL = "NORMAL"
    TRANSPOSE = "TRANSPOSE"

class CopyPasteRequest(BaseModel):
    source: GridRange = Field(description="The source range to copy")
    destination: GridRange = Field(description="The destination range to paste into")
    pasteType: Optional[PasteType] = Field(default=PasteType.PASTE_NORMAL, description="The type of paste to perform")
    pasteOrientation: Optional[PasteOrientation] = Field(default=PasteOrientation.NORMAL, description="The orientation of the paste")


class Body(BaseModel):
    updateSpreadsheetProperties: Optional[UpdateSpreadsheetPropertiesRequest] = Field(default=None, description="Update spreadsheet properties")
    updateSheetProperties: Optional[UpdateSheetPropertiesRequest] = Field(default=None, description="Update sheet properties")

    addSheet: Optional[AddSheetRequest] = Field(default=None, description="Add a new sheet")
    deleteSheet: Optional[DeleteSheetRequest] = Field(default=None, description="Delete a sheet")
    duplicateSheet: Optional[DuplicateSheetRequest] = Field(default=None, description="Duplicate a sheet")

    addTable: Optional[AddTableRequest] = Field(default=None, description="Add a new table")
    updateTable: Optional[UpdateTableRequest] = Field(default=None, description="Update a table")
    deleteTable: Optional[DeleteTableRequest] = Field(default=None, description="Delete a table")

    insertDimension: Optional[InsertDimensionRequest] = Field(default=None, description="Insert a dimension")
    deleteDimension: Optional[DeleteDimensionRequest] = Field(default=None, description="Delete a dimension")

    findReplace: Optional[FindReplaceRequest] = Field(default=None, description="Find and replace text")
    insertRange: Optional[InsertRangeRequest] = Field(default=None, description="Insert a range of cells")

    mergeCells: Optional[MergeCellsRequest] = Field(default=None, description="Merge cells in a range")
    unmergeCells: Optional[UnmergeCellsRequest] = Field(default=None, description="Unmerge cells in a range")

    cutPaste: Optional[CutPasteRequest] = Field(default=None, description="Cut and paste a range of cells")
    copyPaste: Optional[CopyPasteRequest] = Field(default=None, description="Copy and paste a range of cells")
