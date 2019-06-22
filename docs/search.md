# Search engine

- `OR`, ` ` (and), `()` (brackets), and `"` (quotation mark) are supported
- Various `is:` shorthands
- `=`, `~` (regular expression), `>`, `>=`, `<`, `<=`
- `NULL` (does not exist or empty string), `NOW`, `(+/-)(number)(unit)` for time-related fields, e.g. `+1h`

## Supported shorthands (`is:`)

- `is:duplicate` -- filters only duplicates (by `front` field)
- `is:distinct` -- filters only distinct entries by `key` field; or if there is no `key`, by `front` field
- `is:due` -- filters `nextReview:NOW`
- `is:leech` -- filters `srsLevel:0`
- `is:new` -- filters `nextReview:NULL`
- `is:marked` -- filters `tag=marked`
- `is:random` -- equivalent to `sortBy:random`

## Searching syntax

- Time-related fields (`created`, `modified`, `due`, `nextReview`)
    - `(+/-)(number)(unit)`, e.g. `+1h`
    - `NOW`
    - `due` is equivalent to `nextReview`
    - `:` is equivalent to `<=` for `nextReview` or `due`; and `>=` for `created` or `modified`
- Number-related fields (`srsLevel`)
    - `>`, `>=`, `<`, `<=`, `=` is supported. `:` is equivalent to `:`.
    - `NULL` as value means, does not exist
- Data fields (`front`, `back`, `tag`), including custom sockets (e.g. `pinyin`)
    - `:` (substring), `=` (equals), `~` (regular expression), `NULL` (does not exist)
- `-entry` or `-field:entry` for negation
- `OR` and `()` is also supported. ` ` means AND.
- Sorting operators
    - `sortBy:` for ascending sorting
    - `-sortBy:` for decending sorting
    - `sortBy:random` for random shuffle
