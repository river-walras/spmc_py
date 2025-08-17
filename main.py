import threading
import time
import math
from dataclasses import dataclass
from typing import List, TYPE_CHECKING
from spmc_py import SPMCQueue

@dataclass
class Msg:
    ts_ns: int
    idx: int

class Statistic:
    def __init__(self):
        self.vec: List[int] = []
    
    def reserve(self, size: int):
        pass  # Python lists don't need pre-allocation
    
    def size(self) -> int:
        return len(self.vec)
    
    def add(self, v: int):
        self.vec.append(v)
    
    def print_stats(self):
        n = len(self.vec)
        print(f"cnt: {n}")
        if n == 0:
            return
            
        first = self.vec[0]
        self.vec.sort()
        total = sum(self.vec)
        mean = total / n
        
        var = sum((v - mean) ** 2 for v in self.vec) / n
        sd = math.sqrt(var)
        
        print(f"min: {self.vec[0]}")
        print(f"max: {self.vec[-1]}")
        print(f"first: {first}")
        print(f"mean: {mean:.2f}")
        print(f"sd: {sd:.2f}")
        print(f"1%: {self.vec[n * 1 // 100]}")
        print(f"10%: {self.vec[n * 10 // 100]}")
        print(f"50%: {self.vec[n * 50 // 100]}")
        print(f"90%: {self.vec[n * 90 // 100]}")
        print(f"99%: {self.vec[n * 99 // 100]}")

MAX_I = 1000000  # Reduced for Python performance
if TYPE_CHECKING:
    q: SPMCQueue[Msg] = SPMCQueue(1024)
else:
    q = SPMCQueue(1024)

def read_thread(tid: int):
    stat = Statistic()
    stat.reserve(MAX_I)
    count = 0
    reader = q.get_reader()
    
    while True:
        msg = reader.read()
        if msg is None:
            continue
            
        now = time.time_ns()
        latency = now - msg.ts_ns
        stat.add(latency)
        count += 1
        
        assert msg.idx >= count - 1
        
        if msg.idx >= MAX_I - 1:
            break
    
    # Stagger output timing
    time.sleep(tid)
    print(f"tid: {tid}, drop cnt: {MAX_I - count}, latency stats:")
    stat.print_stats()
    print()

def write_thread():
    for i in range(MAX_I):
        msg = Msg(ts_ns=time.time_ns(), idx=i)
        q.write(msg)

def performance_test():
    print("SPMC Queue Performance Test")
    print("=" * 30)
    print(f"Testing with {MAX_I} messages")
    
    # Start writer thread
    writer = threading.Thread(target=write_thread)
    
    # Start 4 reader threads
    readers = []
    for i in range(4):
        reader_thread = threading.Thread(target=read_thread, args=(i,))
        readers.append(reader_thread)
    
    # Start all threads
    for reader in readers:
        reader.start()
    writer.start()
    
    # Wait for completion
    for reader in readers:
        reader.join()
    writer.join()
    

def basic_test():
    """Basic functionality test"""
    print("Basic SPMC Queue Test")
    print("=" * 20)
    
    queue = SPMCQueue(64)
    
    # Test basic write/read
    test_msg = Msg(ts_ns=time.time_ns(), idx=0)
    queue.write(test_msg)
    reader = queue.get_reader()
    msg = reader.read()
    print(f"Basic test: received message with idx={msg.idx if msg else 'None'}")
    
    # Test read_last
    for i in range(5):
        queue.write(Msg(ts_ns=time.time_ns(), idx=i + 10))
    
    last_msg = reader.read_last()
    print(f"Read last: idx={last_msg.idx if last_msg else 'None'}")
    print()

def main():
    basic_test()
    performance_test()
    print("All tests completed!")

if __name__ == "__main__":
    main()
