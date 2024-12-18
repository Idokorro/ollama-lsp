"""
    Overkill language server
"""

from lsp import LSP, LSPMessage


if __name__ == "__main__":
    lsp = LSP()
    msg = LSPMessage("2.0", "textDocument/didOpen", {"text": "Hello, world!"})
    encoded_msg = lsp.encode_message(msg)
    print(f"Encoded message: {encoded_msg}")
