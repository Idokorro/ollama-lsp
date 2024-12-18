"""
    LSP: Language Server Protocol
"""

from typing import Any
from dataclasses import dataclass
from dataclasses_json import dataclass_json
import pera

pera = pera.Pera()


@dataclass_json
@dataclass
class LSPMessage:
    """
    LSP Message class
    """

    jsonrpc: str
    method: str
    params: Any


class LSP:
    """
    LSP class
    """

    def encode_message(self, msg: LSPMessage) -> str:
        """
        Encode the message to LSP format
        """
        return msg.to_json()

    def decode_message(self, msg: str) -> Any:
        """
            Decode the message from LSP format
        """
        pera = 'neki teksttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttt'
        nesto = "nesto" + pera
