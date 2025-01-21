#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdbool.h>
#include <pthread.h>
#include "semaphore.h"

// Semafory
Semaphore sem_mutex;
Semaphore sem_agent, tobacco, paper, match;
Semaphore sem_tobacco, sem_paper, sem_match;

// Sdílené příznaky
bool tobFree = false, paperFree = false, matchesFree = false;

void* pusherA(void* arg) {
    while (1) {
        semaphore_wait(&sem_tobacco);
        semaphore_wait(&sem_mutex);

        if (paperFree) {
            paperFree = false;
            semaphore_signal(&match); // Pustí kuřáka s matches
        } else if (matchesFree) {
            matchesFree = false;
            semaphore_signal(&paper); // Pustí kuřáka s paper
        } else {
            tobFree = true; // Tabák je volný
        }
        semaphore_signal(&sem_mutex);
    }
    return NULL;
}

void* pusherB(void* arg) {
    while (1) {
        semaphore_wait(&sem_paper);
        semaphore_wait(&sem_mutex);

        if (tobFree) {
            tobFree = false;
            semaphore_signal(&match); // Pustí kuřáka s matches
        } else if (matchesFree) {
            matchesFree = false;
            semaphore_signal(&tobacco); // Pustí kuřáka s tobacco
        } else {
            paperFree = true; // Papír je volný
        }
        semaphore_signal(&sem_mutex);
    }
    return NULL;
}

void* pusherC(void* arg) {
    while (1) {
        semaphore_wait(&sem_match);
        semaphore_wait(&sem_mutex);

        if (tobFree) {
            tobFree = false;
            semaphore_signal(&paper); // Pustí kuřáka s paper
        } else if (paperFree) {
            paperFree = false;
            semaphore_signal(&tobacco); // Pustí kuřáka s tobacco
        } else {
            matchesFree = true; // Zápalky jsou volné
        }
        semaphore_signal(&sem_mutex);
    }
    return NULL;
}

void* smoker_with_tobacco(void* arg) {
    while (1) {
        semaphore_wait(&tobacco);
        printf("Smoker with tobacco smokes.\n");
        sleep(2); // Simulace kouření
        semaphore_signal(&sem_agent); // Uvolní agenta
    }
    return NULL;
}

void* smoker_with_paper(void* arg) {
    while (1) {
        semaphore_wait(&paper);
        printf("Smoker with paper smokes.\n");
        sleep(2);
        semaphore_signal(&sem_agent);
    }
    return NULL;
}

void* smoker_with_matches(void* arg) {
    while (1) {
        semaphore_wait(&match);
        printf("Smoker with matches smokes.\n");
        sleep(2);
        semaphore_signal(&sem_agent);
    }
    return NULL;
}

void* agent_function(void* arg) {
    while (1) {
        semaphore_wait(&sem_agent);     
        int choice = rand() % 3;
        switch (choice) {
            case 0:
                printf("Agent places tobacco and paper on the table.\n");
                semaphore_signal(&sem_tobacco);  
                semaphore_signal(&sem_paper);    
                break;
            case 1:
                printf("Agent places tobacco and matches on the table.\n");
                semaphore_signal(&sem_tobacco);  
                semaphore_signal(&sem_match);  
                break;
            case 2:
                printf("Agent places paper and matches on the table.\n");
                semaphore_signal(&sem_paper);    
                semaphore_signal(&sem_match);  
                break;
        }
    }
}

int main(int argc, char *argv[]) {
    // Inicializace semaforů
    semaphore_init(&sem_agent, 1);
    semaphore_init(&sem_tobacco, 0);
    semaphore_init(&sem_paper, 0);
    semaphore_init(&sem_match, 0);
    semaphore_init(&tobacco, 0);
    semaphore_init(&paper, 0);
    semaphore_init(&match, 0);
    semaphore_init(&sem_mutex, 1);

    pthread_t p1, p2, p3, s1, s2, s3, a;

    // Vytvoření vláken pro pusheři
    pthread_create(&p1, NULL, pusherA, NULL);
    pthread_create(&p2, NULL, pusherB, NULL);
    pthread_create(&p3, NULL, pusherC, NULL);

    // Vytvoření vláken pro kuřáky
    pthread_create(&s1, NULL, smoker_with_tobacco, NULL);
    pthread_create(&s2, NULL, smoker_with_paper, NULL);
    pthread_create(&s3, NULL, smoker_with_matches, NULL);

    pthread_create(&a, NULL, agent_function, NULL);

    pthread_join(p1, NULL);
    pthread_join(p2, NULL);
    pthread_join(p3, NULL);
    pthread_join(s1, NULL);
    pthread_join(s2, NULL);
    pthread_join(s3, NULL);
    pthread_join(a, NULL);

    return 0;
}



//gcc -o smokers smokers.c semaphore.c -lpthread
// .\smokers.exe