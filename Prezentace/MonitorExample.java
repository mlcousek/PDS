class Counter {
    private int count = 0;
    private final int limit;

    public Counter(int limit) {
        this.limit = limit;
    }

    public synchronized void increment() {
        count++;
        System.out.println("Incremented count to: " + count);

        // Pokud hodnota dosáhne limitu, upozorní čekající vlákna
        if (count >= limit) {
            notifyAll();
        }
    }

    public synchronized void waitForLimit() {
        try {
            // Čeká, dokud hodnota čítače nedosáhne limitu
            while (count < limit) {
                System.out.println(Thread.currentThread().getName() + " is waiting...");
                wait();
            }
            System.out.println(Thread.currentThread().getName() + " has been notified! Count reached: " + count);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}

public class MonitorExample {
    public static void main(String[] args) {
        Counter counter = new Counter(5); // Nastavíme limit na 5

        // Vlákno, které čeká na dosažení limitu
        Thread waitingThread = new Thread(counter::waitForLimit, "WaitingThread");

        // Vlákno, které provádí inkrementy
        Thread incrementingThread = new Thread(() -> {
            for (int i = 0; i < 6; i++) {
                counter.increment();
                try {
                    Thread.sleep(1000); // Pauza mezi inkrementy
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }
        });

        waitingThread.start();
        incrementingThread.start();
    }
}
