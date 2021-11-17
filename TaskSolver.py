
# by Jakub Grzana
# piece of code that can automatize solving number of isolated tasks, with multiprocessing
# TaskSolver, once created, can be "runned" multiple times

import multiprocessing
import traceback

def subprocess(func, in_queue, out_queue):
    while True:
        obj = in_queue.get()
        result = (None,-1)
        try:
            result = (func(obj[0]), obj[1])
        except Exception as e:
            traceback.print_exc()
            print("EXCEPTION " + str(e) + " IN SUBPROCESS IS IGNORED, FIX YOUR CODE DUDE")
        finally:
            out_queue.put(result)

class TaskSolver:
    def run(self, tasks):
        real_tasks = [ (tasks[i], i) for i in range(0, len(tasks)) ]
        for task in real_tasks: self.in_queue.put(task)
        real_output = [ self.out_queue.get() for task in real_tasks ]
        real_output.sort(key = lambda item: item[1])
        return [ item[0] for item in real_output ]
    def __init__(self, func, num = multiprocessing.cpu_count()):
        self.in_queue = multiprocessing.Queue()
        self.out_queue = multiprocessing.Queue()
        self.processes = [ multiprocessing.Process(target=subprocess, args=(func,self.in_queue, self.out_queue,)) for i in range(0,num) ]
        for proc in self.processes: proc.start()
    def __del__(self):
        for proc in self.processes: proc.terminate()

'''
def f(num):
    return num*2

if __name__ == '__main__':
    solver = TaskSolver(f)
    numbers = [ i for i in range(1,100) ]
    res = solver.run(numbers)
    print(res)
    del solver # if you don't remove solver at the end, it won't be destroyed on it's own and program will never halt
'''