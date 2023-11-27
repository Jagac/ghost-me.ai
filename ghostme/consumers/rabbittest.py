from multiprocessing import Process
import sys
import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR))

from rabbit.mq import MQConsumer

c1 = MQConsumer(queue_name="udemy_courses_1")
c2 = MQConsumer(queue_name="udemy_courses_2")


if __name__ == '__main__':
    subscriber_list = []
    subscriber_list.append(c1)
    subscriber_list.append(c2)

    process_list = []
    for sub in subscriber_list:
        process = Process(target=sub.consume)
        process.start()
        process_list.append(process)

    for process in process_list:
        process.join()