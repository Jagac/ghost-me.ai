import json
import os
import sys
from multiprocessing import Process

import polars as pl

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CURRENT_DIR))

from rabbit.mq import MQConsumer


class Udemy1Consumer(MQConsumer):
    def __init__(self, queue_name) -> None:
        super().__init__(queue_name)
    
    def on_msg_received(self, ch, method, properties, body):
        # transformations go here
        df1 = pl.DataFrame()

        file = json.loads(body)
        for i in file:
            print(i)
            
        self.logger.info(f"Received course data {df1.shape}")

    def consume_json(self):
        self.channel.basic_consume(
            queue=self.queue_name,
            auto_ack=True,
            on_message_callback=self.on_msg_received,
        )
        self.channel.start_consuming()



class Udemy2Consumer(MQConsumer):
    def __init__(self, queue_name) -> None:
        super().__init__(queue_name)
    
    def on_msg_received(self, ch, method, properties, body):
        # transformations go here
        df1 = pl.DataFrame()

        file = json.loads(body)
        for i in file:
            print(i)
            
        self.logger.info(f"Received course data {df1.shape}")

    def consume_json(self):
        self.channel.basic_consume(
            queue=self.queue_name,
            auto_ack=True,
            on_message_callback=self.on_msg_received,
        )
        self.channel.start_consuming()
        
        

if __name__ == '__main__':
    c1 = Udemy1Consumer(queue_name="udemy_courses_1")
    c2 = Udemy2Consumer(queue_name="udemy_courses_2")
    
    subscriber_list = []
    subscriber_list.append(c1)
    subscriber_list.append(c2)

    process_list = []
    for sub in subscriber_list:
        process = Process(target=sub.consume_json)
        process.start()
        process_list.append(process)

    for process in process_list:
        process.join()