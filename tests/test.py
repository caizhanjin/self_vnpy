from multiprocessing import Process
import os
import time


def run_proc(name):
    time.sleep(3)
    print('Run child process %s (%s)...' % (name, os.getpid()))


if __name__ == '__main__':
    print('Parent process %s.' % os.getpid())
    processes = []
    for i in range(5):
        p = Process(target=run_proc, args=('test',))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
    print('Process end.')
