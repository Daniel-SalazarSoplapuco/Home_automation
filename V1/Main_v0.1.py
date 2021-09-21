import asyncio
import random
import datetime as dt
import time as tm
from gpiozero import MotionSensor

async def motion(queue):
    Radar = MotionSensor(20)

    while True:
        Radar.wait_for_inactive()
        await queue.put("[Motion]: Detected at date [{}]".format(dt.datetime.now()))
        await asyncio.sleep(2)
        


async def consume(queue):
    while True:
        # wait for an item from the producer
        item = await queue.get()

        # process the item
        print('received {}'.format(item))
        # simulate i/o operation using sleep
        await asyncio.sleep(random.random())

        # Notify the queue that the item has been processed
        queue.task_done()


async def run():
    queue = asyncio.Queue()
    # schedule the consumer
    consumer = asyncio.ensure_future(consume(queue))
    # run the producer and wait for completion
    await motion(queue)
    # wait until the consumer has processed all items
    await queue.join()
    # the consumer is still awaiting for an item, cancel it
    consumer.cancel()


loop = asyncio.get_event_loop()
loop.run_until_complete(run())
loop.close()