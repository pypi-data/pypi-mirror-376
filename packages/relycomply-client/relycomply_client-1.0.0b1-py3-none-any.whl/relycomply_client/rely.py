from relycomply_client.configuration_sources import StandardConfiguration
from relycomply_client.gql_client import RelyComplyGQLClient
from .sync import sync
from .render import render
from .watch import watch_sync
from .cli import RelyComplyCLI
from .environment import environment_app
import typer
from .turbo import turbo, turbo_help_text
from .introspect import introspect

help_text = """
The RelyComply client
"""

app = typer.Typer(rich_markup_mode="markdown", help=help_text)

app.command()(sync)
app.command("watch")(watch_sync)
app.command()(render)
app.command(hidden=True)(introspect)


def version_callback(value: bool):
    if value:
        import importlib.metadata

        __version__ = importlib.metadata.version("relycomply_client")
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def common(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        callback=version_callback,
        help="Show the current version of the relycomply client",
    ),
):
    pass


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def cli(ctx: typer.Context):
    """
    A convinient CLI for interacting with the RelyComply GraphQL API
    """
    configuration = StandardConfiguration()
    configuration.validate()
    gql_client = RelyComplyGQLClient(configuration=configuration)
    cli = RelyComplyCLI(gql_client=gql_client)
    cli.run_command(ctx.args)


app.add_typer(environment_app, name="environment")

app.command(help=turbo_help_text())(turbo)


def main():
    app()
