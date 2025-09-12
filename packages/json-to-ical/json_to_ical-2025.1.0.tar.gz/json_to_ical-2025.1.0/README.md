# PyConAU calendar converter

A cli tool which will take a .json agenda file or url (based on the schema https://c3voc.de/schedule/schema.json) 
and convert it to an .ics calendar file.

As used by https://pretalx.com/

## Local environment setup

    $ uv sync --all-groups


## Testing 

    $ uv run pytest
   
### Testing with specific python versions

    $ uv run --python 3.9 pytest
    $ uv run --python 3.10 pytest
    $ uv run --python 3.11 pytest
    $ uv run --python 3.12 pytest
    $ uv run --python 3.13 pytest

### Tested dependencies

| Python version | ical   | pydantic |
|----------------|--------|----------|
| 3.9            | 4.5.4  | 1.10.22  |
| 3.10           | 8.2.0  | 2.11.7   |
| 3.11           | 8.2.0  | 2.11.7   |
| 3.12           | 11.0.0 | 2.11.7   |
| 3.13           | 11.0.0 | 2.11.7   |
