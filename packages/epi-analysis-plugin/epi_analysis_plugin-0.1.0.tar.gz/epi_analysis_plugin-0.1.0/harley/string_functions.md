## anti_trim(expr)

```python
def anti_trim(expr: List[IntoExpr]) -> IntoExpr:
    """
    Replaces all whitespace to a single space from a string, then trims leading and trailing spaces.
    """
    expr = parse_into_expr(expr)
    return register_plugin(
        args=[expr],
        symbol="anti_trim",
        is_elementwise=True,
        lib=lib,
    )
```

##  remove_all_whitespace(expr)

```python
def remove_all_whitespace(expr: IntoExpr) -> IntoExpr:
    """
    Removes all whitespace from a string.
    """
    expr = parse_into_expr(expr)
    return register_plugin(
        args=[expr],
        symbol="remove_all_whitespace",
        is_elementwise=True,
        lib=lib,
    )
```

## remove_non_word_characters(expr)

```python
def remove_non_word_characters(expr: IntoExpr) -> IntoExpr:
    """
    Removes all non-word characters. "Word characters" are [\w\s], i.e. alphanumeric, whitespace, and underscore ("_").
    """
    expr = parse_into_expr(expr)
    return register_plugin(
        args=[expr],
        symbol="remove_non_word_characters",
        is_elementwise=True,
        lib=lib,
    )
```

##  single_space(expr)

```python
def single_space(expr: IntoExpr) -> IntoExpr:
    """
    Replaces all whitespace to a single space from a string, then trims leading and trailing spaces.
    """
    expr = parse_into_expr(expr)
    return register_plugin(
        args=[expr],
        symbol="single_space",
        is_elementwise=True,
        lib=lib,
    )
```
