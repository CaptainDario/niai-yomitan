# niai-yomitan

Repo to convert the niai db to a yomitan kanji dictionary for use in DaKanji

## Installation

Make sure uv is installed on your system and run

``` bash
uv sync
```

## Usage

Run this command to parse the PDF database and convert it to a yomitan kanji dictionary.

``` bash
uv run niai_to_yomitan.py
```

## Original data

https://github.com/mrahhal/niai/blob/main/backend/src/Niai/data/kanjis.json
