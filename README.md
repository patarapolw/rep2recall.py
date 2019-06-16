# Rep2Recall Python version

Rep2Recall with SQLite, powered by Python Flask server

Download: <https://github.com/patarapolw/rep2recall-py/releases>

[![](/screenshots/0.png)](https://youtu.be/LlFLVNLxqcQ)

## Features

- Uses SQLite all the way, so editable via programming. (SQLite path can be viewed at Settings.)
- Full range of CSS and JavaScript enabled, as defined by latest web browser. ([Chromium](https://www.chromium.org/Home) for [Electron](https://electronjs.org/docs/tutorial/about).) It is possible without clashing without the UI due to `<iframe srcdoc="html">`
- Exposes CORS-enabled web API.
- Easy to add media files, by copying to `media/` folder. It will be available as `/media/file.ext`

## API

The API is accessible at `http://localhost:34972`. See [/api.md](/api.md)

## Development mode

Rep2Recall can be run without Electron using either `yarn run dev` or (`yarn run js:dev` and `yarn run py:dev` in different terminals).

Environmental variables can be set as following in `.env`

```
PORT=34972
COLLECTION=user.db
```
