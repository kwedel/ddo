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
    style: Optional[str] = None  # Retained but unused in current parsing
    example: Optional[str] = None


class WordEntry(NamedTuple):
    """
    Represents a complete dictionary entry for a word
    """

    word: str
    part_of_speech: str
    inflections: str
    etymology: Optional[str]
    definitions: List[WordDefinition]
    synonyms: List[str]
    phon: Optional[str] = None


BASE_URL = "https://ws.dsl.dk/ddo/query"


def lookup(word: str) -> List[WordEntry]:
    """
    Lookup a word in the Danish dictionary

    :param word: Word to lookup
    :return: List of WordEntry with word details (handles multiple matches)
    """
    params = {"q": word}

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
    except requests.RequestException as e:
        rich.print(f"[bold red]Error fetching dictionary data:[/] {e}")
        sys.exit(1)

    soup = BeautifulSoup(response.text, "html.parser")

    entries = []
    for ar in soup.find_all("span", class_="ar"):
        head = ar.find("span", class_="head")
        k_span = head.find("span", class_="k") if head else None
        word_text = k_span.get_text(strip=True) if k_span else word

        pos_tag = ar.find("span", class_="pos")
        part_of_speech = pos_tag.get_text(strip=True) if pos_tag else "N/A"

        phon_tag = ar.find("span", class_="phon")
        phon = phon_tag.get_text(separator=" ", strip=True) if phon_tag else None

        inflections_tag = ar.find("span", class_="m")
        inflections = inflections_tag.get_text(strip=True) if inflections_tag else ""

        def_container = ar.find("span", class_="def")
        etymology = None
        definitions = []
        synonyms = []

        if def_container:
            etym_tag = def_container.find("span", class_="etym")
            if etym_tag:
                etym_text = etym_tag.get_text()
                etymology = " ".join(
                    etym_text.split()
                )  # Normalize spacing by collapsing multiple spaces

            # Parse inner definitions (direct children of def_container)
            for def_inner in def_container.find_all(
                "span", class_="def", recursive=False
            ):
                level_tag = def_inner.find("span", class_="l")
                dtrn_tag = def_inner.find("span", class_="dtrn")

                if dtrn_tag:
                    level = level_tag.get_text(strip=True) if level_tag else ""
                    text = dtrn_tag.get_text(separator=" ", strip=True)
                    # Note: <span class="co"> (commentary) is already included in text

                    example_tag = def_inner.find("span", class_="ex")
                    example = example_tag.get_text(strip=True) if example_tag else None

                    # Collect synonyms/related from onyms within this definition
                    onyms_tags = def_inner.find_all(
                        "span", class_=lambda x: x and "onyms" in " ".join(x)
                    )
                    for onyms in onyms_tags:
                        for syn_k in onyms.find_all("span", class_="k"):
                            syn_text = syn_k.get_text(strip=True)
                            if syn_text and syn_text.lower() != word_text.lower():
                                synonyms.append(
                                    " ".join(syn_text.split())
                                )  # Normalize any spacing in synonyms

                    definition = WordDefinition(
                        level=level, text=text, style=None, example=example
                    )
                    definitions.append(definition)

        # Deduplicate synonyms
        synonyms = list(set(synonyms))

        entry = WordEntry(
            word=word_text,
            part_of_speech=part_of_speech,
            phon=phon,
            inflections=inflections,
            etymology=etymology,
            definitions=definitions,
            synonyms=synonyms,
        )
        entries.append(entry)

    return entries


def display(entries: List[WordEntry]) -> None:
    """
    Display word data in a rich, formatted manner

    :param entries: List of WordEntry to display
    """
    if not entries:
        console = Console()
        console.print("[red]No results found.[/]")
        return

    console = Console()

    for entry in entries:
        # Word header
        console.print(
            Panel(
                Text.assemble(
                    (entry.word, "bold cyan"), " ", (entry.part_of_speech, "italic")
                ),
                title="Dictionary Entry",
                border_style="blue",
            )
        )

        # Inflections
        if entry.inflections:
            console.print(f"[bold]Inflections:[/] {entry.inflections}")

        # Udtale (pronunciation)
        if entry.phon is not None:
            console.print("[bold]Udtale:[/] " + rich.markup.escape(entry.phon))
        else:
            console.print("[bold]Udtale:[/] N/A")

        # Etymology
        if entry.etymology:
            console.print("[bold]Etymology:[/] " + rich.markup.escape(entry.etymology))

        # Definitions
        if entry.definitions:
            console.print("\n[bold underline]Definitions:[/]")
            for definition in entry.definitions:
                definition_text = Text()

                # Add level if exists
                if definition.level:
                    definition_text.append(f"{definition.level} ", style="green")

                # Add definition text
                definition_text.append(rich.markup.escape(definition.text))

                # Style is not used (commentary is embedded in text)

                console.print(definition_text)

                # Add example if exists
                if definition.example:
                    console.print(
                        f"  [dim italic]Example: {rich.markup.escape(definition.example)}[/]"
                    )
        else:
            console.print("[italic]No definitions found.[/]")

        # Synonyms
        if entry.synonyms:
            console.print("\n[bold]Synonyms & Related:[/] " + ", ".join(entry.synonyms))

        console.print("\n")  # Space between entries
