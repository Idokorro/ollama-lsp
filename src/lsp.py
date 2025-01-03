import logging

from dataclasses import dataclass
from typing import Any, Optional, List
from dataclasses_json import dataclass_json

from ollama import chat, ChatResponse


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


class LSP:
    def __init__(self):
        self.documents: dict[str, List[str]] = {}

        self.message: LSPRequest | None = None
        self.content_length: int = -1

        self.initialized: bool = False
        self.running: bool = True
        self.shutting_down: bool = False

        import time
        self.start_time = time.time()

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
            case "exit":
                return self.handle_exit()
            case _:
                err = self.check_initialized()
                if err is not None:
                    return err

                err = self.check_shutting_down()
                if err is not None:
                    return err

                return self.handle_document_sync()
        
    def handle_initialize(self):
        if not self.initialized:
            if self.message is not None and self.message.params is not None:
                logger.info(f"Connected to: {self.message.params['clientInfo']['name']} {self.message.params['clientInfo']['version']}")
            else:
                logger.info("Connected to unknown client")
            self.initialized = True
            return LSPResponse(
                jsonrpc="2.0",
                id=self.get_msg_id(),
                result={
                    "capabilities": {
                        "textDocumentSync": {
                            "openClose": True,
                            "change": 2
                        },
                        "completionProvider": {}
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
        logger.info("Shutting down server")

        self.shutting_down = True

        return LSPResponse(
            jsonrpc="2.0",
            id=self.get_msg_id()
        )

    def handle_exit(self):
        logger.info("Exiting server")

        self.running = False

        return None

    def handle_document_sync(self):
        if self.message is None:
            return LSPResponse(
                jsonrpc="2.0",
                id=self.get_msg_id(),
                error={ "code": -32603, "message": "Server error" }
            )

        response = None

        match self.message.method:
            case "textDocument/didOpen":
                if self.message.params is not None:
                    logger.info(f"Document opened - {self.message.params['textDocument']['uri']}")

                    doc = self.message.params['textDocument']['uri']
                    content = self.message.params['textDocument']['text'].splitlines(True)

                    self.documents[doc] = content

                    logger.debug(f"Documents: {self.documents.keys()}")
                    logger.debug(f"Document content: {self.documents[doc]}")

            case "textDocument/didClose":
                if self.message.params is not None:
                    logger.info(f"Document closed - {self.message.params['textDocument']['uri']}")

                    doc = self.message.params['textDocument']['uri']
                    del self.documents[doc]

                    logger.debug(f"Documents: {self.documents.keys()}")

            case "textDocument/didChange":
                if self.message.params is not None:
                    logger.info(f"Document changed - {self.message.params['textDocument']['uri']}")

                    doc = self.message.params['textDocument']['uri']
                    changes = self.message.params['contentChanges']
                    
                    response = self.handle_document_change(doc, changes)

                    logger.debug(f"Document content: {self.documents[doc]}")
            case "textDocument/completion":
                if self.message.params is not None:
                    logger.info(f"Completion requested - {self.message.params['textDocument']['uri']}")

                    doc = self.message.params['textDocument']['uri']
                    position = self.message.params['position']

                    response = self.handle_completion(doc, position)

        return response

    def handle_completion(self, doc: str, position: dict[str, int]):
        document = self.documents[doc]
        
        to_complete = document[:position["line"]]
        to_complete.append(document[position["line"]][:position["character"]])
        to_complete = "".join(to_complete)
        last_word = to_complete.split()[-1]

        prompt = "Complete the following text: " + to_complete
        ai_resp: ChatResponse = chat(model="llama3.2:3b", messages=[{ "role": "user", "content": prompt }])
        
        return LSPResponse(
            jsonrpc="2.0",
            id=self.get_msg_id(),
            result={
                "isIncomplete": False,
                "items": [
                    {
                        "label": last_word,
                        "kind": 15,
                        "documentation": ai_resp.message.content,
                        "insertText": ai_resp.message.content,
                        "insertTextFormat": 2,
                        "insertTextMode": 1
                    }
                ]
            }
        )

    def handle_document_change(self, doc: str, changes: List[dict[str, Any]]):
        if doc not in self.documents:
            logger.error(f"Document not found: {doc}")

            return LSPResponse(
                jsonrpc="2.0",
                id=self.get_msg_id(),
                error={ "code": -32001, "message": "Document not found" }
            )

        content = self.documents[doc]

        start_char = 0
        start_line = 0

        for change in changes:
            start_char = change["range"]["start"]["character"]
            start_line = change["range"]["start"]["line"]
            end_char = change["range"]["end"]["character"]
            end_line = change["range"]["end"]["line"]

            new_chars = change["text"].splitlines(True)
            if len(new_chars) == 0:
                new_chars = [""]

            try:
                if end_line >= len(content):
                    end_line = len(content) - 1
                    start_line = len(content) - 2
                    start_char = len(content[start_line])
                    end_of_line = ""
                else:
                    end_of_line = content[end_line][end_char:]

                while start_line < end_line:
                    content.pop(start_line + 1)
                    end_line -= 1

                new_char = new_chars.pop(0)
                while len(new_chars) >= 1:
                    content[start_line] = content[start_line][:start_char] + new_char
                    content.insert(start_line + 1, "")
                    start_line += 1
                    start_char = 0
                    new_char = new_chars.pop(0)

                
                if new_char.startswith("\n"):
                    content[start_line] = content[start_line][:start_char] + new_char[0]
                    content.insert(start_line + 1, new_char[1:] + end_of_line)
                else:
                    content[start_line] = content[start_line][:start_char] + new_char + end_of_line

            except Exception as e:
                logger.error(f"Error changing document: {e}")

        self.documents[doc] = content

    def check_initialized(self):
        if not self.initialized:
            logger.error("Server not initialized")

            return LSPResponse(
                jsonrpc="2.0",
                id=self.get_msg_id(),
                error={ "code": -32002, "message": "Server not initialized" }
            )

        return None

    def check_shutting_down(self):
        if self.shutting_down:
            logger.error("Received a message while server is shutting down")

            return LSPResponse(
                jsonrpc="2.0",
                id=self.get_msg_id(),
                error={ "code": -32600, "message": "Server is shutting down" }
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

            if self.message is not None:
                logger.info(f"Message method: {self.message.method}")
            logger.debug(f"Message: {self.message}")
        else:
            logger.error("Message not complete")
