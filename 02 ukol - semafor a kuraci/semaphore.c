#include "semaphore.h"

// Inicializace semaforu
void semaphore_init(Semaphore* sem, int initial_value) {
    atomic_store(&sem->value, initial_value);
}

// Čekání na semafor
void semaphore_wait(Semaphore* sem) {
    int expected;
    do {
        // Atomicky načteme hodnotu semaforu
        expected = atomic_load(&sem->value);
        // Pokud je hodnota větší než 0, pokusíme se ji snížit
        if (expected > 0) {
            // Atomicky snížíme hodnotu semaforu
            if (atomic_compare_exchange_weak(&sem->value, &expected, expected - 1)) {
                return;  // Úspěšně jsme získali přístup
            }
        }
    } while (1);  // Čekáme dokud semafor nebude k dispozici
}

// Uvolnění semaforu
void semaphore_signal(Semaphore* sem) {
    atomic_fetch_add(&sem->value, 1);
}
