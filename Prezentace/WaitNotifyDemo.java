class WaitNotifyExample {
    private boolean ready = false;

    public synchronized void doWait() {
        while (!ready) {
            try {
                System.out.println("Waiting...");
                wait(); // Čekání na notify nebo notifyAll
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
        System.out.println("Notified, proceeding!");
    }

    public synchronized void doNotify() {
        ready = true;
        notify(); // nebo použijte notifyAll() pro probuzení všech čekajících vláken
        System.out.println("Notification sent!");
    }
}

public class WaitNotifyDemo {
    public static void main(String[] args) {
        WaitNotifyExample example = new WaitNotifyExample();

        Thread waitingThread = new Thread(example::doWait);
        Thread notifyingThread = new Thread(example::doNotify);

        waitingThread.start();
        try { Thread.sleep(1000); } catch (InterruptedException ignored) {} // Pauza pro zajištění, že vlákno čeká
        notifyingThread.start();
    }
}
