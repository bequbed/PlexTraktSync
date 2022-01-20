from functools import wraps
from os import environ

import click

from plextraktsync.commands.self_update import enable_self_update, self_update
from plextraktsync.commands.sync import sync
from plextraktsync.commands.trakt_login import trakt_login
from plextraktsync.commands.unmatched import unmatched
from plextraktsync.commands.watch import watch
from plextraktsync.factory import factory

CONFIG = factory.config()


def command():
    """
    Wrapper to lazy load commands when commands being executed only
    """

    def decorator(fn):
        @click.command()
        @wraps(fn)
        def wrap(*args, **kwargs):
            import importlib

            name = fn.__name__
            module = importlib.import_module(f'.commands.{name}', package=__package__)
            cmd = getattr(module, name)
            cmd(*args, **kwargs)

        return wrap

    return decorator


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """
    Plex-Trakt-Sync is a two-way-sync between trakt.tv and Plex Media Server
    """
    if not ctx.invoked_subcommand:
        sync()


@command()
@click.option(
    "--sort",
    type=click.Choice(["size", "date", "url"], case_sensitive=False),
    default="size",
    show_default=True, help="Sort mode"
)
@click.option(
    "--limit",
    type=int,
    default=20,
    show_default=True, help="Limit entries to be printed"
)
@click.option(
    "--reverse",
    is_flag=True,
    default=False,
    help="Sort reverse"
)
@click.argument("url", required=False)
def cache():
    """
    Manage and analyze Requests Cache.
    """
    pass


@command()
@click.option('--confirm', is_flag=True, help='Confirm the dangerous action')
@click.option('--dry-run', is_flag=True, help='Do not perform delete actions')
def clear_collections():
    """
    Clear Movies and Shows collections in Trakt
    """

    pass


@command()
def info():
    """
    Print application and environment version info
    """

    pass


@command()
@click.argument('input', nargs=-1)
@click.option(
    "--watched-shows",
    type=bool,
    default=False,
    is_flag=True,
    help="Print Trakt watched_shows and exit"
)
def inspect():
    """
    Inspect details of an object
    """

    pass


@command()
def login():
    """
    Log in to Plex and Trakt if needed
    """
    pass


@command()
@click.option("--username", help="Plex login", default=lambda: environ.get("PLEX_USERNAME", CONFIG["PLEX_USERNAME"]))
@click.option("--password", help="Plex password", default=lambda: environ.get("PLEX_PASSWORD", None))
def plex_login():
    """
    Log in to Plex Account to obtain Access Token. Optionally can use managed user on servers that you own.
    """
    pass


cli.add_command(cache)
cli.add_command(clear_collections)
cli.add_command(info)
cli.add_command(inspect)
cli.add_command(login)
cli.add_command(plex_login)
if enable_self_update():
    cli.add_command(self_update)
cli.add_command(sync)
cli.add_command(trakt_login)
cli.add_command(unmatched)
cli.add_command(watch)
