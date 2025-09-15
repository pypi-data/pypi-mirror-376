import sys
import typer
from relycomply_client.configuration_sources import StandardConfiguration
from relycomply_client.gql_client import RelyComplyGQLClient
from graphql import print_schema


def introspect():
    """
    Introspect the GraphQL schema and print it to stdout
    """
    configuration = StandardConfiguration()
    configuration.validate()
    gql_client = RelyComplyGQLClient(configuration=configuration)
    if gql_client.schema:
        print(print_schema(gql_client.schema))
    else:
        print("Could not retrieve schema.", file=sys.stderr)
        raise typer.Exit(code=1)
