class MyCounter {
    private int count = 0;

    // synchronized metoda pro zajištění bezpečného přístupu
    public synchronized void increment() {
        count++;
    }

    public int getCount() {
        return count;
    }
}


public class SynchronizedExample {
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