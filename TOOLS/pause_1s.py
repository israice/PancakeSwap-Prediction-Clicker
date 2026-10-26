
import sys
import time

DELAY_SECONDS = 1.0


try:
    time.sleep(DELAY_SECONDS)
except KeyboardInterrupt:
    sys.exit(130)
