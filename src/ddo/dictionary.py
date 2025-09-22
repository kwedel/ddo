import requests
from bs4 import BeautifulSoup
from typing import List, NamedTuple, Optional
import sys
import rich
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


class WordDefinition(NamedTuple):
    """
    Represents a single definition of a word
    """

    level: str
    text: str
    style: Optional[str] = None
    example: Optional[str] = None


class WordEntry(NamedTuple):
    """
    Represents a complete dictionary entry for a word
    """

    word: str
    part_of_speech: str
    phon: str
    inflections: str
    etymology: Optional[str]
    definitions: List[WordDefinition]
    synonyms: List[str]


BASE_URL = "https://ws.dsl.dk/ddo/query"


def lookup(word: str) -> WordEntry:
    """
    Lookup a word in the Danish dictionary

    :param word: Word to lookup
    :return: WordEntry with word details
    """
    params = {"q": word}  # , "app": "ios", "version": "2.1.2"}

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
    except requests.RequestException as e:
        rich.print(f"[bold red]Error fetching dictionary data:[/] {e}")
        sys.exit(1)

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract word
    word_text = soup.find("span", class_="k")
    word_text = word_text.text if word_text else word

    # Extract part of speech
    pos_tag = soup.find("span", class_="pos")
    part_of_speech = pos_tag.text if pos_tag else "N/A"

    # Extract
    phon_tag = soup.find("span", class_="phon")
    phon_tag = phon_tag.text if phon_tag else "N/A"

    # Extract inflections
    inflections_tag = soup.find("span", class_="m")
    inflections = inflections_tag.text if inflections_tag else ""

    # Extract etymology
    etymology_tag = soup.find("span", class_="etym")
    etymology = etymology_tag.text if etymology_tag else None

    # Extract definitions
    definitions = []
    for def_tag in soup.find_all("span", class_="def"):
        level_tag = def_tag.find("span", class_="l")
        dtrn_tag = def_tag.find("span", class_="dtrn")

        if level_tag and dtrn_tag:
            # Extract style if exists
            style_tag = def_tag.find("span", class_="style")
            style = style_tag.text if style_tag else None

            # Extract example if exists
            example_tag = def_tag.find("span", class_="ex")
            example = example_tag.text if example_tag else None

            definition = WordDefinition(
                level=level_tag.text, text=dtrn_tag.text, style=style, example=example
            )
            definitions.append(definition)

    # Extract synonyms
    synonyms = []
    synonyms_tag = soup.find("span", class_="onyms synonyms")
    if synonyms_tag:
        synonyms = [syn.text for syn in synonyms_tag.find_all("span", class_="k")]

    return WordEntry(
        word=word_text,
        part_of_speech=part_of_speech,
        phon=phon_tag,
        inflections=inflections,
        etymology=etymology,
        definitions=definitions,
        synonyms=synonyms,
    )


def display(word_data: WordEntry):
    """
    Display word data in a rich, formatted manner

    :param word_data: WordEntry to display
    """
    console = Console()

    # Word header
    console.print(
        Panel(
            Text.assemble(
                (word_data.word, "bold cyan"), " ", (word_data.part_of_speech, "italic")
            ),
            title="Dictionary Entry",
            border_style="blue",
        )
    )

    # Inflections
    if word_data.inflections:
        console.print(f"[bold]Inflections:[/] {word_data.inflections}")

    # Udtale
    if word_data.phon:
        console.print("[bold]Udtale:[/] " + rich.markup.escape(f"{word_data.phon}"))

    # Etymology
    if word_data.etymology:
        console.print(f"[bold]Etymology:[/] {word_data.etymology}")

    # Definitions
    console.print("\n[bold underline]Definitions:[/]")
    for definition in word_data.definitions:
        definition_text = Text()

        # Add level if exists
        if definition.level:
            definition_text.append(f"{definition.level} ", style="green")

        # Add definition text
        definition_text.append(definition.text)

        # Add style if exists
        if definition.style:
            definition_text.append(f" [{definition.style}]", style="italic dim")

        console.print(definition_text)

        # Add example if exists
        if definition.example:
            console.print(f"  [dim italic]Example: {definition.example}[/]")

    # Synonyms
    if word_data.synonyms:
        console.print("\n[bold]Synonyms:[/] " + ", ".join(word_data.synonyms))
