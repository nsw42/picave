import json
import pathlib
from urllib.parse import urlparse

import jsonschema
import requests


def read_from_uri(url, schema_leaf):
    """
    Create and initialise a JsonFeed object from the url specified on the command-line
    This may be a file:// or http[s]://
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        # TODO: Error handling
        raise
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
        handle = open(filename)
    except OSError:
        # TODO: Error handling
        raise
    content = json.load(handle)
    return _validate_content(content, schema_leaf)


def _read_from_url(url, schema_leaf):
    """
    Create and initialise a JsonFeed object by reading the given URL
    """
    response = requests.get(url)
    if response.status_code != 200:
        # TODO: Error handling
        raise Exception("Could not read %s" % url)
    return _validate_content(response.json(), schema_leaf)


def _validate_content(json_content, schema_leaf):
    # Schema validation
    schema_filename = pathlib.Path(__file__).parent / schema_leaf
    schema = json.load(open(schema_filename))
    # throws on validation error
    jsonschema.validate(instance=json_content, schema=schema)

    #  Schema validation successful; now initialise items array
    return json_content
