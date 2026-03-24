import click

from scripts.check_link_text import check_link_text
from scripts.check_urls import check_urls
from scripts.make_collection_csv import get_collection_urls


@click.group
def cli():
    pass


cli.add_command(get_collection_urls, name="get-collection-urls")
cli.add_command(check_link_text, name="check-link-text")
cli.add_command(check_urls, name="check-urls")

if __name__ == "__main__":
    cli()
