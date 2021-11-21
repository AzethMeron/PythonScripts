
from multiprocessing import Process, Queue
import multiprocessing
import math

def function(x):#, d):
    numbers = set()
    steps = 0
    while x != 1:
        if x in numbers: return (-1) * steps
        #if x in d: return steps + d[x]
        numbers.add(x)
        if x % 2 == 0: # even
            x = x / 2
        else:
            x = 3*x + 1
        steps = steps +1
    return steps

def compute_A(minv, maxv): # Complexity 3x+1 estimated to A*log(n, 2)
    # It isn't precise, but it's pretty accurate in big picture. A = 7 to 9
    total_steps = 0
    last_percentage = 0
    for i in range(minv,maxv):
        percentage = round(100*(i-minv)/(maxv-minv),1)
        #if percentage > last_percentage: print(percentage)
        last_percentage = percentage
        total_steps = total_steps + function(i)
    total_num = maxv-minv
    avg_steps = total_steps / total_num
    avg_n = sum( range(minv, maxv) ) / total_num
    avg_logn = math.log(avg_n, 2)
    return avg_steps / avg_logn

if __name__ == '__main__':
    cpu_count = multiprocessing.cpu_count()
    for i in range(10,30):
        minv = pow(10,i)
        maxv = minv + 10000
        print(f"Set {i}: " + str(compute_A(minv, maxv)))