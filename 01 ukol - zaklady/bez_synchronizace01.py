from threading import Thread
import time
import random

# Sdílený čítač
counter: int = 0
m :int = 2 #kolikrat se ma jeden proces inkrementovat

# Funkce, kterou každé vlákno provede
def increment_counter() -> None:
    global counter
    for _ in range(m):
        time.sleep(random.uniform(0.1, 0.5))  
        local_counter = counter              
        time.sleep(random.uniform(0.1, 0.5))  
        local_counter += 1                   
        time.sleep(random.uniform(0.1, 0.5))  
        counter = local_counter   

# Funkce pro vytvoření a spuštění n vláken
def run_threads(n) -> None:
    threads = []
    for _ in range(n):
        thread = Thread(target=increment_counter)
        threads.append(thread)
        thread.start()

    # Počkáme na dokončení všech vláken
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    n = 200  #PARAMETR VLAKEN
    run_threads(n)
    
    print(f"Expected value: {n * m}")
    print(f"Real value: {counter}")
