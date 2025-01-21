#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdbool.h>
#include <pthread.h>
#include "semaphore.h"

#define NUM_THREADS 5

Semaphore sem;

void* thread_function(void* arg) {
    int id = *((int*)arg);
    printf("Thread %d: ceka na semafor...\n", id);
    semaphore_wait(&sem);
    
    // Kritická sekce
    printf("Thread %d: ziskal semafor!\n", id);
    usleep(1000); // Simulace práce //999 čeká získá uvolňuje dokola 1000 všichni čekaj a pak získá a uvolňuje dokola
    printf("Thread %d: uvolnuje semafor.\n", id);
    
    semaphore_signal(&sem);
    return NULL;
}

int main() {
    pthread_t threads[NUM_THREADS];
    int thread_ids[NUM_THREADS];

    // Inicializace semaforu s hodnotou 1
    semaphore_init(&sem, 1);

    // Vytvoření vláken
    for (int i = 0; i < NUM_THREADS; i++) {
        thread_ids[i] = i + 1; // Uložení ID vlákna
        pthread_create(&threads[i], NULL, thread_function, &thread_ids[i]);
    }

    // Čekání na dokončení vláken
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    return 0;
}

//gcc -o semaphoreTest semaphoreTest.c semaphore.c -lpthread
// .\semaphoreTest.exe