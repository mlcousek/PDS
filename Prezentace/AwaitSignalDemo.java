import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

class AwaitSignalExample {
    private final Lock lock = new ReentrantLock();
    private final Condition condition = lock.newCondition();
    private boolean ready = false;

    public void waitForSignal() {
        lock.lock();
        try {
            while (!ready) {
                System.out.println("Waiting for the signal...");
                condition.await();
            }
            System.out.println("Received signal, proceeding!");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } finally {
            lock.unlock();
        }
    }

    public void sendSignal() {
        lock.lock();
        try {
            ready = true;
            condition.signal(); // nebo použijte condition.signalAll() pro probuzení všech čekajících vláken
            System.out.println("Signal sent!");
        } finally {
            lock.unlock();
        }
    }
}

public class AwaitSignalDemo {
    public static void main(String[] args) {
        AwaitSignalExample example = new AwaitSignalExample();

        Thread waitingThread = new Thread(example::waitForSignal);
        Thread signalingThread = new Thread(example::sendSignal);

        waitingThread.start();
        try { Thread.sleep(1000); } catch (InterruptedException ignored) {} // Pauza pro zajištění, že vlákno čeká
        signalingThread.start();
    }
}
