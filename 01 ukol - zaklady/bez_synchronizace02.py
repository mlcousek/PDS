#ThreadPoolExecutor
from concurrent.futures import ThreadPoolExecutor
import time
import random

# Sdílený čítač
counter: int = 0
m :int = 1 #kolikrat se ma jeden proces inkrementovat

# Funkce, kterou každé vlákno provede
def increment_counter(i) -> None:
    global counter
    for _ in range(m):
        time.sleep(random.uniform(0.1, 0.5))  
        local_counter = counter              
        time.sleep(random.uniform(0.1, 0.5))  
        local_counter += 1                   
        time.sleep(random.uniform(0.1, 0.5))  
        counter = local_counter               

# Funkce pro vytvoření a spuštění vláken pomocí ThreadPoolExecutor
def run_threads_threadpool(n) -> None:
    with ThreadPoolExecutor(max_workers=50) as executor: #zalezi kolik nastavit to max_workers vetsi presnost = vetsi cas
        executor.map(increment_counter, range(n))

if __name__ == "__main__":
    n = 200  #PARAMETR VLAKEN
    run_threads_threadpool(n)
    
    print(f"Expected value: {n * m}")
    print(f"Real value: {counter}")

