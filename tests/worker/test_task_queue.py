from worker.task_queue import get_queue

def test_queue(arg1, arg2):
    print(arg1 + '.' + arg2)

get_queue().add_task(test_queue, ['1', '2'], queue='test_tq')
get_queue().pop_and_execute(queue='test_tq')