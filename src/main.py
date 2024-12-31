import logging
import sys
from lsp import LSP, LSPMessage

logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(filename='/home/igor/work/lsp/logs/lsp.log', level=logging.DEBUG)
    
    lsp = LSP()
    
    for line in sys.stdin:
        lsp.handle_message(line)

if __name__ == "__main__":
    main()
