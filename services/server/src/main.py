import os
import sys

import logger
import server

SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")
SERVER_PORT = int(os.environ.get("SERVER_PORT", 8080))
STORAGE_PATH = os.environ.get("STORAGE_PATH", "/storage")
QUORUM_MIN = int(os.environ.get("AGENCY_QUORUM_MIN", 1))


def main():
    logger.init()
    s = server.Server(SERVER_HOST, SERVER_PORT, STORAGE_PATH, QUORUM_MIN)
    try:
        s.run()
    except Exception as e:
        logger.error("server-run", logger.LogResult.fail, "err", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
