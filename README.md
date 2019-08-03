# Rep2Recall

Rep2Recall with SQLite, powered by Python Flask server

Download: <https://github.com/patarapolw/rep2recall-py/releases>

[![](/screenshots/0.png)](https://youtu.be/VDRyn7FUy8k)

## Features

- Intuitive "Repeat to Recall" [spaced repetition memorization](https://en.wikipedia.org/wiki/Spaced_repetition) inspired by <https://www.wanikani.com/>
- Uses SQLite all the way, so editable via programming. (SQLite path can be viewed at Settings.)
- Full range of CSS and JavaScript enabled, as defined by latest web browser. ([Chromium](https://www.chromium.org/Home) for [Electron](https://electronjs.org/docs/tutorial/about).) It is possible without clashing with the UI due to `<iframe srcdoc="html">`
- Intuitive and powerful [search engine](/docs/search.md)
- Exposes CORS-enabled web API.
- Easy to add media files, by copying to `media/` folder. It will be available as `/media/file.ext`

## API

The API is accessible at `http://localhost:34972`. See [/docs/api.md](/docs/api.md)

## Development mode

Environmental variables can be set as following in `.env`

```
PORT=34972
COLLECTION=user.db
```

Tested with NPM and Poetry on macOS. Run `poetry install` and `npm run dev`.

## Build instruction

- Build <https://github.com/patarapolw/rep2recall.front> with `npm run build` and copy the output to `/www/`
- `npm run py:build`
- `npm run build`
