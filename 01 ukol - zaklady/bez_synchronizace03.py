#Gevent pripomina virtualni vlakna
import gevent
from gevent import monkey
import random
import time

# Patch pro kompatibilitu s green threads
monkey.patch_all()

# Sdílený čítač
counter: int = 0
m :int = 5 #kolikrat se ma jeden proces inkrementovat


# Funkce, kterou každé vlákno provede
def increment_counter() -> None:
    global counter
    for _ in range(m):
        gevent.sleep(random.uniform(0.1, 0.5))  
        local_counter = counter              
        gevent.sleep(random.uniform(0.1, 0.5))  
        local_counter += 1                   
        gevent.sleep(random.uniform(0.1, 0.5))  
        counter = local_counter               

# Funkce pro spuštění vláken pomocí green threads
def run_threads_gevent(n):
    jobs = [gevent.spawn(increment_counter) for _ in range(n)]
    gevent.joinall(jobs)

if __name__ == "__main__":
    n = 20  #PARAMETR VLAKEN
    run_threads_gevent(n)
    
    print(f"Expected value: {n * m}")
    print(f"Real value: {counter}")


