import logging
from dataclasses import dataclass
from typing import Any, Optional

from dataclasses_json import dataclass_json


logger = logging.getLogger(__name__)


@dataclass_json
@dataclass
class LSPRequest:
    jsonrpc: str = "2.0"
    id: Optional[int | str] = None
    method: str = ""
    params: Optional[Any] = None


@dataclass_json
@dataclass
class LSPResponse:
    jsonrpc: str = "2.0"
    id: Optional[int | str] = None
    result: Optional[Any] = None
    error: Optional[Any] = None


@dataclass_json
@dataclass
class LSPNotification:
    jsonrpc: str = "2.0"
    method: str = ""
    params: Optional[Any] = None


class LSP:
    def __init__(self):
        self.message: LSPRequest | LSPNotification | None = None
        self.content_length: int = -1
        self.initialized: bool = False
        self.running: bool = True

    def encode_message(self, message: LSPResponse) -> str:
        msg = message.to_json()
        return f"Content-Length: {len(msg)}\r\n\r\n{msg}"

    def handle_message(self, msg: str):
        self.decode_message(msg)

        if self.message is None:
            return None 

        match self.message.method:
            case "initialize":
                return self.handle_initialize()
            case "shutdown":
                return self.handle_shutdown()
            case _:
                err = self.check_initialized()
                if err is not None:
                    return err
                """ TO-DO """
                return None
        
    def handle_initialize(self):
        if not self.initialized:
            if type(self.message) is LSPRequest and self.message.params is not None:
                logger.debug(f"Connected to: {self.message.params['clientInfo']['name']} {self.message.params['clientInfo']['version']}")
            else:
                logger.debug("Connected to unknown client")
            self.initialized = True
            return LSPResponse(
                jsonrpc="2.0",
                id=self.get_msg_id(),
                result={
                    "capabilities": {

                    },
                    "serverInfo": { 
                        "Name": "Overkill LSP",
                        "Version": "over 9000"
                    }
                }
            )
        else:
            logger.error("Server already initialized")
            return LSPResponse(
                jsonrpc="2.0",
                id=self.get_msg_id(),
                error={ "code": -32600, "message": "Already initialized" }
            )

    def handle_shutdown(self):
        logger.debug("Shutting down server")
        """ TO-DO """
        return LSPResponse(
            jsonrpc="2.0",
            id=self.get_msg_id(),
            result=None
        )

    def check_initialized(self):
        if not self.initialized:
            return LSPResponse(
                jsonrpc="2.0",
                id=self.get_msg_id(),
                error={ "code": -32002, "message": "Server not initialized" }
            )

        return None

    def get_msg_id(self):
        if self.message is None:
            return None

        if type(self.message) is LSPRequest:
            return self.message.id

        return None

    def decode_content_length(self, msg: str):
        self.content_length = int(msg.split(" ")[1])

        logger.debug(f"Content-Length: {self.content_length}")

    def decode_message(self, msg: str):
        if len(msg) == self.content_length:
            self.message = LSPRequest.from_json(msg)
            self.content_length = -1

            logger.debug(f"Message: {self.message}")
        else:
            logger.error("Message not complete")
