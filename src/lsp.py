import logging
from dataclasses import dataclass
from typing import Any, Optional

from dataclasses_json import dataclass_json


logger = logging.getLogger(__name__)


@dataclass_json
@dataclass
class LSPMessage:
    jsonrpc: str
    id: Optional[int]
    method: str
    params: Optional[Any]


class LSP:
    def __init__(self):
        self.message = None
        self.content_length = 0
        self.buffer = ""

    def encode_message(self, message: LSPMessage) -> str:
        msg = message.to_json()
        return f"Content-Length: {len(msg)}\r\n\r\n{msg}"

    def handle_message(self, msg: str):
        if msg.startswith("Content-Length:"):
            self.content_length = int(msg.split(" ")[1])
            logger.debug(f"Content-Length: {self.content_length}")
        elif msg != "\r\n":
            if len(msg) == self.content_length:
                self.buffer += msg
                self.message = LSPMessage.from_json(self.buffer)
                self.buffer = ""
                logger.debug(f"Message: {self.message}")
            else:
                self.buffer += msg
                self.content_length -= len(msg)
                logger.debug(f"Buffer: {self.buffer}")
                logger.debug(f"Content-Length: {self.content_length}")
