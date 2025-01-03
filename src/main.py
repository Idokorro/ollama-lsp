import logging
import sys
from lsp import LSP


logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(filename='/home/igor/work/lsp/logs/lsp.log', level=logging.ERROR)
    
    lsp = LSP()
    
    while lsp.running:
        if lsp.content_length > 0:
            line = sys.stdin.read(lsp.content_length)
       
            response = lsp.handle_message(line)
            
            if response is not None:
                logger.debug(f"Response: {response}")
                print(lsp.encode_message(response))
                sys.stdout.flush()
        else:
            line = sys.stdin.readline()
            if line.startswith("Content-Length: "):
                lsp.decode_content_length(line)
                sys.stdin.readline()

    if lsp.shutting_down:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
