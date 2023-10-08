import json
import logging
import pathlib
from urllib.parse import urlparse

import jsonschema
import requests


class JsonFeedException(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = message


class NotFoundError(JsonFeedException):
    pass


class InputMalformedError(JsonFeedException):
    pass


def read_from_uri(url, schema_leaf):
    """
    Create and initialise a JsonFeed object from the url specified on the command-line
    This may be a file:// or http[s]://
    """
    try:
        parsed = urlparse(url)
    except ValueError as e:
        raise NotFoundError(f"Count not parse {url}") from e
    if parsed.scheme == 'file':
        # read the file directory
        return _read_from_file(parsed.path, schema_leaf)
    else:
        return _read_from_url(url, schema_leaf)


def _read_from_file(filename, schema_leaf):
    """
    Create and initialise a JsonFeed object by reading a local file
    """
    try:
        handle = open(filename, encoding='utf-8')
    except OSError as e:
        raise NotFoundError(f"File '{filename}' not found") from e
    content = json.load(handle)
    return _validate_content(content, schema_leaf, filename)


def _read_from_url(url, schema_leaf):
    """
    Create and initialise a JsonFeed object by reading the given URL
    """
    response = requests.get(url)
    if response.status_code != 200:
        raise NotFoundError(f"Could not read {url}")
    return _validate_content(response.json(), schema_leaf, url)


def _validate_content(json_content, schema_leaf, source):
    # Schema validation
    schema_filename = pathlib.Path(__file__).parent / schema_leaf
    schema = json.load(open(schema_filename, encoding='utf-8'))
    try:
        jsonschema.validate(instance=json_content, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        logging.error(f"Schema validation error: {e}")
        raise InputMalformedError(f"{source} is malformed") from e

    #  Schema validation successful; now initialise items array
    return json_content
