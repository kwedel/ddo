import click

from .autocomplete import get_completions
from .dictionary import display, lookup


@click.command()
@click.argument("word", type=str, shell_complete=get_completions)
def cli(word):
    """
    Lookup a word in the Danish dictionary

    Example: ord pære
    """
    word_data = lookup(word)
    display(word_data)


if __name__ == "__main__":
    cli()
