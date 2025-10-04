# Den Danske Ordbog CLI

A command-line interface (CLI) tool for looking up words in [**Den Danske Ordbog (ddo)**](https://ordnet.dk).
It fetches definitions, etymologies, inflections, synonyms, and more. This tool is not affiliated with [Det Danske Sprog- og Litteraturselskab](https://dsl.dk/).

Also, the code is mainly written by LLMs.

---

## Features

- Word lookup with full dictionary entries  
- Definitions, styles, and usage examples  
- Inflections and etymology information  
- Phonetic transcriptions when available  
- Synonyms and related words  
- Shell autocomplete support for word suggestions  
- Nicely formatted output with [Rich](https://github.com/Textualize/rich)  

---

## Installation and usage

The package is available on PyPI. The recommended way to install it is with [uv](https://github.com/astral-sh/uv):

```bash
uv tool install ddo
ddo eksorbitant
```

---

## Autocomplete

The CLI supports autocomplete using DDO’s livesearch API. To enable it, you need to configure your shell for Click’s completion:

1. Enable completion for your shell (bash, zsh, or fish) using:

   ``` bash
   _DDO_COMPLETE=bash_source ddo > ~/.ddo-complete.sh
   echo 'source ~/.ddo-complete.sh' >> ~/.bashrc
   ```
   (replace bash_source with zsh_source or fish_source depending on your shell)

2. Restart your shell or re-source your configuration file.

Once enabled, pressing Tab while typing a word will fetch suggestions from the dictionary’s autocomplete service.