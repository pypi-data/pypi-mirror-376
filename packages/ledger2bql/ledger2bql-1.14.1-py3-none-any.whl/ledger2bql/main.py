"""
CLI runner for Ledger2BQL utility.
"""

import sys
from importlib.metadata import PackageNotFoundError
from dotenv import find_dotenv, load_dotenv
import click

from .balance import bal_command
from .register import reg_command
from .query import query_command
from .lots import lots_command


class AliasedGroup(click.Group):
    """A click Group that supports command aliases."""

    def get_command(self, ctx, cmd_name):
        """Get the command by name or alias."""
        # Try the normal way first
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        # Check for aliases
        aliases = {"b": "bal", "r": "reg", "q": "query", "l": "lots"}

        if cmd_name in aliases:
            return click.Group.get_command(self, ctx, aliases[cmd_name])

        return None


@click.group(cls=AliasedGroup, invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show the version and exit.")
@click.pass_context
def cli(ctx, version):
    """Translate Ledger CLI query syntax into BQL"""
    if version:
        try:
            from importlib.metadata import version as get_version

            v = get_version("ledger2bql")
        except PackageNotFoundError:
            v = "local"
        click.echo(f"ledger2bql v{v}")
        sys.exit(0)

    # Initialize environment variables by loading .env files in the
    # parent directories.
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path, override=True)

    # If no subcommand was called, show help
    if ctx.invoked_subcommand is None:
        try:
            from importlib.metadata import version as get_version

            v = get_version("ledger2bql")
        except PackageNotFoundError:
            v = "local"
        click.echo(f"ledger2bql v{v}")
        click.echo(ctx.get_help())
        click.echo(
            "\nNote: 'b' is an alias for 'bal', 'r' is an alias for 'reg', 'q' is an alias for 'query', and 'l' is an alias for 'lots'"
        )
        click.echo(
            "You can call any command with '--help' to get the list of available parameters and options."
        )
        sys.exit(0)


# Add the subcommands
cli.add_command(bal_command)
cli.add_command(reg_command)
cli.add_command(query_command)
cli.add_command(lots_command)


def main():
    """main entry point"""
    cli()


if __name__ == "__main__":
    main()
