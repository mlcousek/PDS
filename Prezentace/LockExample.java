import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

class MyCounter {
    private int count = 0;
    private final Lock lock = new ReentrantLock();

    public void increment() {
        lock.lock(); // zamkne přístup k části kódu
        try {
            count++;
        } finally {
            lock.unlock(); // odemkne přístup
        }
    }

    public int getCount() {
        return count;
    }
}

public class LockExample {
    public static void main(String[] args) throws InterruptedException {
        MyCounter counter = new MyCounter();

        // vytvoření dvou vláken, která volají metodu increment
        Thread t1 = new Thread(() -> {
            for (int i = 0; i < 1000; i++) {
                counter.increment();
            }
        });

        Thread t2 = new Thread(() -> {
            for (int i = 0; i < 1000; i++) {
                counter.increment();
            }
        });

        t1.start();
        t2.start();

        // počká na dokončení obou vláken
        t1.join();
        t2.join();

        System.out.println("Final Count: " + counter.getCount()); // Výstup: 2000
    }
}
