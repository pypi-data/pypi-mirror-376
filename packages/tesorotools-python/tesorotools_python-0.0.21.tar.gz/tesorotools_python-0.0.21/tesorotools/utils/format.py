from typing import Any

import pandas as pd

from tesorotools.utils.matplotlib import format_annotation


def format_table(
    table: pd.DataFrame, format_dict: dict[str, dict[str, Any]]
) -> pd.DataFrame:
    """Formats a pandas dataframe to get it ready for being rendered into a .docx file.

    Parameters
    ----------
    table : pd.DataFrame
    format_dict : dict[str, dict[str, Any]]
        Each key in the dictionary is a column in the dataframe, each value is a dictionary with 3 possible entries: "scale" (integer, default=1), "decimals" (integer, default=0), "units" (string, default="").

    Returns
    -------
    pd.DataFrame
        The formatted dataframe
    """
    for column, fmt in format_dict.items():
        if pd.api.types.is_numeric_dtype(table[column]):
            scale = fmt.get("scale", 1)
            table[column] = table[column] / scale
            table[column] = table[column].apply(
                lambda x: format_annotation(
                    value=x,
                    decimals=fmt.get("decimals", 0),
                    units=fmt.get("units", ""),
                )
            )

    for column in table.columns:
        table[column] = table[column].astype(str)
    return table
