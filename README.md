# Overkill LSP for simple text

Total overkill LSP for simple text editing. Uses ollama in the background to generate completions. Works only with text files (*.txt).

Very bad. :) Everything needs to be improved.

## Setup

## Ollama
First setup "nvidia-container-toolkit".

Run server:
* `docker run --rm -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama`

Pull model:
* `ollama pull <model>`

List of [models](https://ollama.com/library).

## Neovim
Copy `load_ai_lsp.lua` to nvim config directory and load it.

Change path to this directory in `load_ai_lsp.lua`. It's hardcoded. :)

## Python
Put `.venv` in this directory and install reqs.

## Usage
Open a text file in Neovim and start typing. You should see completions.
