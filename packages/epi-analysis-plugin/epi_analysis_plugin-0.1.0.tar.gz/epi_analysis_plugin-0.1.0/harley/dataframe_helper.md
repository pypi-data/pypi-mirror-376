## column_to_list(df, column)

```python
def column_to_list(df: PolarsFrame, column: str) -> List:
    """
    Takes a PolarsFrame and a column name, extracts the specified column as a list, and
    returns it.

    :param df: PolarsFrame
    :type df: PolarsFrame
    :param column: The name of the column in
    the Polars DataFrame (`df`) that you want to extract and convert into a Python list
    :type column: str
    :return: a list of values from the specified column in the PolarsFrame dataframe.
    """
    if isinstance(df := df.select(column), LazyFrame):
        df = df.collect()
    series = df.select(column).to_series()
    return series.to_list()
```


##  two_columns_to_dictionary(df, key_col_name, value_col_name, allow_duplicates_keys=False)

```python
def two_columns_to_dictionary(
    df: DataFrame,
    key_col_name: str,
    value_col_name: str,
    allow_duplicates_keys: bool = False,
) -> Dict[Any, Any]:
    """
    Converts two columns from a DataFrame into a dictionary,
    with one column as keys and the other as values,
    handling potential issues like duplicate keys and
    non-hashable types.

    :param df: A DataFrame containing the data you want to convert into a dictionary
    :type df: DataFrame
    :param key_col_name: The name of the column in the DataFrame that will be used as the key in the resulting dictionary.
    This column should contain unique values that will serve as the keys in the dictionary mapping.
    :type key_col_name: str
    :param value_col_name: The name of the column in the DataFrame that contains the
    values you want to map to the keys in the dictionary.
    :type value_col_name: str
    :param allow_duplicates_keys: A boolean flag that determines whether duplicate keys are
    allowed in the resulting dictionary. If set to `False` (default), the function will raise a
    `ValueError` if duplicate keys are found in the specified key column, defaults to False
    :type allow_duplicates_keys: bool (optional)
    :return: Converts the two specified columns from the DataFrame into a dictionary
    where the key is the value from the key column and the value is the value from the value column.
    """
    df = df.select(key_col_name, value_col_name)
    key_dtype = df.dtypes[0]
    if key_dtype.is_nested():
        raise ValueError(
            f"Column {key_col_name} is of type {df.dtypes[0]} will not return a hashable type.",
            f"Therefore {key_col_name} cannot provide an acceptable key",
        )
    if key_dtype in [Object, Unknown]:
        raise ValueError(
            f"Column {key_col_name} is of type {df.dtypes[0]} and may not return a hashable type.",
            f"Therefore {key_col_name} cannot provide an acceptable key.",
        )
    if not allow_duplicates_keys:
        if df.filter(col(key_col_name).is_duplicated()).height > 0:
            raise ValueError(
                "Duplicate records found in key column.",
                "Duplicate keys will be overwritten and de-duplicated unpredicatbly.",
                "To allow duplicate keys, set `allow_duplicate_keys` to True",
                "Some of the duplicates:",
                column_to_list(
                    df.filter((col(key_col_name).is_duplicated())), key_col_name
                )[:3],
            )
    df = df.to_dicts()
    return {row[key_col_name]: row[value_col_name] for row in df}
```
