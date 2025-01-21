#ifndef SEMAPHORE_H
#define SEMAPHORE_H


#include <stdatomic.h>

typedef struct {
    atomic_int value;
} Semaphore;

void semaphore_init(Semaphore* sem, int initial_value);
void semaphore_wait(Semaphore* sem);
void semaphore_signal(Semaphore* sem);

#endif // SEMAPHORE_H
