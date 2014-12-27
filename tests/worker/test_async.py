import worker.async_task as async_task
from worker.task_queue import async_queue

def test(num):
    return num * num

# tid = async_task.async(test, (2,))
# print(tid)
# tid2 = async_task.async(test, (2,))
# print(tid2)

# print(async_task.query_task(tid))

# print(async_queue.pop_and_execute())

# print(async_task.query_task(tid))
# print(async_task.query_task('e0174d073524773dd9ad0f6cade79ec2191bbb06'))