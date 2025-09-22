import click
from .dictionary import lookup, display
from .autocomplete import get_completions


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
