## `marrow` - minimalist Arrow interop

`marrow` allows building and viewing arrow arrays of different implementations using a unified interface. The motivation behind `marrow` is to allow libraries to target multiple different arrow versions simultaneously.

Supported arrow implementations:

-   `arrow`
-   `arrow2`

The main types are

-   `Array`: an array with owned data
-   `View`: an array with borrowed data
-   `Field`: the data type and metadata of a field
-   `DataType`: data types of arrays

### Conversions

marrow offers conversions between its types and the types of different arrow versions. See the features section how to enable support for a specific version. The following conversion are implemented.

From marrow to arrow:
```rust
TryFrom<marrow::array::Array> for arrow::array::ArrayRef
TryFrom<&marrow::datatypes::Field> for arrow::datatypes::Field
TryFrom<&marrow::datatypes::DataType> for arrow::datatypes::DataType
TryFrom<marrow::datatypes::TimeUnit> for arrow::datatypes::TimeUnit
TryFrom<marrow::datatypes::UnionMode> for arrow::datatypes::UnionMode
```
From arrow to marrow:
```rust
TryFrom<&dyn arrow::array::Array> for marrow::view::View<'_>
TryFrom<&arrow::datatypes::Field> for marrow::datatypes::Field
TryFrom<&arrow::datatypes::DataType> for marrow::datatypes::DataType
TryFrom<arrow::datatypes::TimeUnit> for marrow::datatypes::TimeUnit
TryFrom<arrow::datatypes::UnionMode> for marrow::datatypes::UnionMode
```
For `arrow2` the corresponding conversions are implemented.

For example to access the data in an arrow array:

```rust
use arrow::array::Int32Array;
use marrow::view::View;

// build the arrow array
let arrow_array = Int32Array::from(vec![Some(1), Some(2), Some(3)]);

// construct a view of this array
let marrow_view = View::try_from(&arrow_array as &dyn arrow::array::Array)?;

// access the underlying data
let View::Int32(marrow_view) = marrow_view else { panic!() };
assert_eq!(marrow_view.values, &[1, 2, 3]);
```

Or to build an array:

```rust
use arrow::array::Array as _;
use marrow::array::{Array, PrimitiveArray};

// build the array
let marrow_array = Array::Int32(PrimitiveArray {
    validity: Some(marrow::bit_vec![true, false, true]),
    values: vec![4, 0, 6],
});

// convert it to an arrow array
let arrow_array_ref = arrow::array::ArrayRef::try_from(marrow_array)?;
assert_eq!(arrow_array_ref.is_null(0), false);
assert_eq!(arrow_array_ref.is_null(1), true);
assert_eq!(arrow_array_ref.is_null(2), false);
```

## Features


Supported features:

    - serde: enable Serde serialization / deserialization for schema types (Field, DataType, …). The format will match the arrow crate
    - arrow-{version}: enable conversions between marrow and arrow={version}
    - arrow2-{version}: enable conversions between marrow and arrow2={version}

This crate supports conversions from and to different version of arrow or arrow2. These conversions can be enabled by selecting the relevant features. Any combination of features can be selected, e.g., both arrow-53 and arrow-52 can be used at the same time.

Supported arrow versions:

Feature	Arrow Version
arrow-56	arrow=56
arrow-55	arrow=55
arrow-54	arrow=54
arrow-53	arrow=53
arrow-52	arrow=52
arrow-51	arrow=51
arrow-50	arrow=50
arrow-49	arrow=49
arrow-48	arrow=48
arrow-47	arrow=47
arrow-46	arrow=46
arrow-45	arrow=45
arrow-44	arrow=44
arrow-43	arrow=43
arrow-42	arrow=42
arrow-41	arrow=41
arrow-40	arrow=40
arrow-39	arrow=39
arrow-38	arrow=38
arrow-37	arrow=37
arrow2-0-17	arrow2=0.17
arrow2-0-16	arrow2=0.16

Note, arrow2=0.18 is not supported as the source code was not tagged on GitHub.

Modules

array
    Arrays with owned data
bits
    Helpers to work with bit vectors
datatypes
    Supported data types
error
    Error handling in marrow
types
    Specialized element types of arrays
view
    Arrays with borrowed data

Macros

bit_array
    Build a fixed-size bit array from a sequence of booleans
bit_vec
    Construct a bit vector (Vec<u8>) from a sequence of booleans
