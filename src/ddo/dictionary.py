import requests
from bs4 import BeautifulSoup
from typing import List, NamedTuple, Optional
import sys
import rich
from rich.console import Console
from rich.panel import Panel


class WordDefinition(NamedTuple):
    """
    Represents a single definition of a word
    """

    level: str
    text: str
    style: Optional[str] = None
    example: Optional[str] = None
    indent: int = 0


class WordEntry(NamedTuple):
    """
    Represents a complete dictionary entry for a word
    """

    word: str
    part_of_speech: str
    inflections: str
    etymology: Optional[str] = None
    phon: Optional[str] = None
    definitions: List[WordDefinition] = []
    synonyms: List[str] = []


BASE_URL = "https://ws.dsl.dk/ddo/query"


def parse_definitions(
    container, synonyms: List[str], indent: int, word_text: str
) -> List[WordDefinition]:
    """
    Recursively parse definition spans, handling subdefinitions and collecting synonyms/related terms.
    """
    definitions = []
    for def_span in container.find_all("span", class_="def", recursive=False):
        level_tag = def_span.find("span", class_="l")
        level = level_tag.get_text(strip=True) if level_tag else ""

        dtrn_tag = def_span.find("span", class_="dtrn")
        style = None
        text = ""
        if dtrn_tag:
            full_text = dtrn_tag.get_text(separator=" ", strip=True)
            style_tag = dtrn_tag.find("span", class_="style")
            if style_tag:
                style = style_tag.get_text(strip=True)
                # Remove style from the beginning of the text if present
                if full_text.startswith(style):
                    full_text = full_text[len(style) :].strip()
                else:
                    full_text = full_text.replace(style, "", 1).strip()
                text = " ".join(full_text.split())
            else:
                text = full_text

        example_tag = def_span.find("span", class_="ex")
        example = example_tag.get_text(strip=True) if example_tag else None

        # Collect synonyms/related from onyms within this definition
        onyms_tags = def_span.find_all(
            "span", class_=lambda x: x and "onyms" in " ".join(x or [])
        )
        for onyms in onyms_tags:
            for syn_k in onyms.find_all("span", class_="k"):
                syn_full = syn_k.get_text(separator=" ", strip=True)
                syn_text = " ".join(syn_full.split())
                if syn_text and syn_text.lower() != word_text.lower():
                    synonyms.append(syn_text)

        definition = WordDefinition(
            level=level,
            text=text,
            style=style,
            example=example,
            indent=indent,
        )
        definitions.append(definition)

        # Recurse for subdefinitions
        sub_definitions = parse_definitions(def_span, synonyms, indent + 1, word_text)
        definitions.extend(sub_definitions)

    return definitions


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
                etym_full = etym_tag.get_text(separator=" ", strip=True)
                etymology = " ".join(etym_full.split())  # Normalize spacing

            definitions = parse_definitions(def_container, synonyms, 0, word_text)

        # Deduplicate synonyms
        synonyms = list(set(synonyms))

        entry = WordEntry(
            word=word_text,
            part_of_speech=part_of_speech,
            inflections=inflections,
            etymology=etymology,
            phon=phon,
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

    # Display the primary (first) entry in full
    primary = entries[0]
    # Word header
    console.print(
        Panel(
            f"[bold cyan]{primary.word}[/] [italic]{primary.part_of_speech}[/italic]",
            title="Den Danske Ordbog",
            border_style="blue",
        )
    )

    # Inflections
    if primary.inflections:
        console.print(f"[bold]Bøjning:[/] {primary.inflections}")

    # Udtale (pronunciation)
    if primary.phon is not None:
        console.print(f"[bold]Udtale:[/] {rich.markup.escape(primary.phon)}")
    else:
        console.print("[bold]Udtale:[/] N/A")

    # Etymology
    if primary.etymology:
        console.print(f"[bold]Etymologi:[/] {rich.markup.escape(primary.etymology)}")

    # Definitions
    if primary.definitions:
        console.print("\n[bold underline]Betydninger:[/]")
        for definition in primary.definitions:
            level_part = (
                f"[green]{definition.level}[/green] " if definition.level else ""
            )
            text_part = rich.markup.escape(definition.text)
            style_part = (
                f" [italic][{definition.style}][/italic]" if definition.style else ""
            )
            full_def = f"{level_part}{text_part}{style_part}".strip()
            indent_str = "  " * definition.indent
            console.print(f"{indent_str}{full_def}")

            # Add example if exists
            if definition.example:
                ex_indent = "  " * (definition.indent + 1)
                console.print(
                    f"{ex_indent}[dim italic]Example: {rich.markup.escape(definition.example)}[/dim italic]"
                )
    else:
        console.print("[italic]No definitions found.[/]")

    # Synonyms
    if primary.synonyms:
        console.print(
            f"\n[bold]Synonymer & Relateret:[/] {', '.join(primary.synonyms)}"
        )

    # Other matches if any
    if len(entries) > 1:
        other_words = [entry.word for entry in entries[1:]]
        console.print(f"\n[bold]Andre matches:[/] {', '.join(other_words)}")

    console.print("\n")
