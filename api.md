# Rep2Recall API

## Card editing

### Reading cards

- Endpoint: `/api/editor/`
- Method: `POST`
- Sample body:

```json
{
    "q": "deck:HSK",
    "offset": 10,
    "limit": 10
}
```


### Inserting cards

- Endpoint: `/api/editor/`
- Method: `PUT`
- Sample body:

```json
{
    "create": [
        {
            "front": "foo",
            "back": "bar"
        },
        {
            "front": "baz",
            "note": "baaq"
        }
    ]
}
```
- Sample response

```json
{
    "ids": [3, 4]
}
```

### Updating cards

- Endpoint: `/api/editor/`
- Method: `PUT`
- Sample body:

```json
{
    "ids": [3, 4],
    "update": {
        "deck": "HSK/HSK1"
    }
}
```

### Deleting cards

- Endpoint: `/api/editor/`
- Method: `DELETE`
- Sample body:

```json
{
    "ids": [3, 4]
}
```

### Editing card tags

- Endpoint: `/api/editor/`
- Method: `PUT`
- Sample body:

```json
{
    "ids": [3, 4],
    "tags": ["HSK"],
    "isAdd": true
}
```