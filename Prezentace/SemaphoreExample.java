import java.util.concurrent.Semaphore;

class ResourceAccess {
    private final Semaphore semaphore;

    public ResourceAccess(int permits) {
        this.semaphore = new Semaphore(permits); 
    }

    public void accessResource(String threadName) {
        try {
            System.out.println(threadName + " is trying to access the resource...");
            semaphore.acquire(); // získání povolení (čeká, pokud není dostupné)

            System.out.println(threadName + " has acquired access to the resource.");
            // Simulace práce se zdrojem
            Thread.sleep(2000);

            System.out.println(threadName + " has released the resource.");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } finally {
            semaphore.release(); // uvolnění povolení
        }
    }
}

public class SemaphoreExample {
    public static void main(String[] args) {
        ResourceAccess resource = new ResourceAccess(2); 

        // Vytvoření více vláken pro přístup ke zdroji
        for (int i = 1; i <= 6; i++) { // více vláken než povolení
            final String threadName = "Thread-" + i;
            new Thread(() -> resource.accessResource(threadName)).start();
        }
    }
}
