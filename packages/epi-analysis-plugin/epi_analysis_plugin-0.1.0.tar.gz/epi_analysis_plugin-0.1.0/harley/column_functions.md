## `approx_equal(col_1, col_2, threshold)`

```python
def approx_equal(
    col_1: IntoExpr, col_2: IntoExpr, threshold: Union[float, int]
) -> IntoExpr:
    """
    Compares two columns for approximate equality within a specified threshold.

    :param col_1: The first column or expression that you want to compare for approximate
    equality
    :type col_1: IntoExpr
    :param col_2: The second column or value that you want to
    compare for approximate equality with col_1
    :type col_2: IntoExpr
    :param threshold: Specifies the  maximum allowable difference between the values in `col_1` and `col_2` for them to be considered
    approximately equal.
    :type threshold: Union[float, int]
    :return: boolean typed expression.
    """
    col_1 = parse_into_expr(col_1)
    col_2 = parse_into_expr(col_2)
    return register_plugin(
        args=[col_1, col_2],
        symbol="approx_equal",
        is_elementwise=True,
        lib=lib,
        kwargs={"threshold": float(threshold)},
    )
```

##  multi_equals(cols, val)

```python
def multi_equals(cols: List[str], val: Any) -> Expr:
    """
    Creates a query that checks if multiple columns have a specified value.

    :param cols: List[str]
    :type cols: List[str]
    :param val: The value that you want to compare the columns against in the
    `multi_equals` function
    :type val: Any
    :return: The function `multi_equals` returns an expression that represents the logical AND operation
    of equality checks between the columns specified in the `cols` list and the value `val`.
    """
    query = [pl.col(name) == val for name in cols]
    return pl.all_horizontal(query)
```

##  null_between(col, lower, upper)

```python
def null_between(col: str, lower: str, upper: str) -> Expr:
    """
    The function `null_between` returns an expression to check if a column value falls within a range,
    handling null values appropriately.

    :param col: The column for which you want to check if the values are
    null or fall within a certain range defined by the `lower` and `upper` bounds.
    :type col: str
    :param lower: The lower bound column or value that you want to compare against.
    :type lower: str
    :param upper: The upper bound column or value that you want to compare against
    :type upper: str
    :return: The `null_between` function is returning a polars expression that checks if a column
    `col` falls between two other columns `lower` and `upper`, handling cases where any of the columns
    are null.
    """
    return (
        pl.when(pl.col(lower).is_null() & pl.col(upper).is_null())
        .then(False)
        .when(pl.col(col).is_null())
        .then(False)
        .when(pl.col(lower).is_null())
        .then(pl.col(col) <= pl.col(upper))
        .when(pl.col(upper).is_null())
        .then(pl.col(col) >= pl.col(lower))
        .otherwise(pl.col(col).is_between(pl.col(lower), pl.col(upper)))
    )
```

## snake_case_column_names(df)

```python
def snake_case_column_names(df: PolarsFrame) -> PolarsFrame:
    """
    Takes a PolarsFrame, converts its column names to snake case,
    and returns the modified PolarsFrame.

    :param df: A PolarsFrame object, which can be eith er a LazyFrame or DataFrame.
    :type df: PolarsFrame
    :return: The function `snake_case_column_names` is returning a PolarsFrame with column names
    converted to snake case.
    """
    if isinstance(df, LazyFrame):
        all_column_names = df.collect_schema().names()
    else:
        all_column_names = df.columns
    new_col_names = columns_to_snake_case(all_column_names)
    return df.rename(new_col_names)
```
