import sys
import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR))

from rabbit.mq import MQConsumer

conns = MQConsumer("resume_pdf")
conns.consume_pdf()
