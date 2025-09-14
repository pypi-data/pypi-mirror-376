import json
import click


def print_json(data):
    click.echo(json.dumps(data, indent=2))
