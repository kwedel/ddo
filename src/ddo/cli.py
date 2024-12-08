import click
from .dictionary import lookup, display
from .autocomplete import WordAutocomplete


@click.command()
@click.argument("word", type=str)
def cli(word):
    """
    Lookup a word in the Danish dictionary

    Example: ord pære
    """
    word_data = lookup(word)
    display(word_data)


if __name__ == "__main__":
    cli()
