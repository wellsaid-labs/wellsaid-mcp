# wellsaid_mcp/server.py

from wellsaid_mcp.mcp_server import mcp
import wellsaid_mcp.avatars
import wellsaid_mcp.tts
import wellsaid_mcp.ai_director

import logging
import sys

logging.info("starting mcp server")


def main():
    logging.info("🚀 Starting WellSaid MCP Server...")
    try:
        mcp.run()
    except BrokenPipeError:
        logging.info("Broken pipe error, can be ignored")
        # This happens when Claude closes the stdio pipe.
        # Exit quietly instead of showing a huge traceback.
        sys.exit(0)
    except BaseException as e:
        logging.info("Exception while running mcp server")
        logging.info(e)
        sys.exit(0)
 

if __name__ == "__main__":
    main()
