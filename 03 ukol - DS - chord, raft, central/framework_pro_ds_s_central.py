import threading
import queue
import time
import random

# Třída pro zprávy
class Message:
    def __init__(self, sender_id, recipient_id, message_type, content=None):
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.message_type = message_type
        self.content = content
        
# Třída pro uzly
class Node:
    def __init__(self, node_id, name):
        self.node_id = node_id
        self.name = name
        self.inbox = queue.Queue()
        
        self.running = False
        self.network = None
        
        self.thread = threading.Thread(target=self.run)       
               
    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.inbox.put(None)
        print(f"Node {self.node_id} has been stopped.")
    
    def send_message(self, network, recipient, message_type, content=None):
        message = Message(sender_id=self.node_id, recipient_id=recipient, message_type=message_type, content=content)
        network.deliver_message(message)

    def receive_message(self, message):
        self.inbox.put(message)

    def process_message(self, message):
        if message.message_type == "access_granted":
            self.real_critical_section()
        elif message.message_type == "critical_section":
            self.critical_section()
        elif message.message_type == "send_custom_message":
            print(f"Node {self.node_id} received custom message: {message.content}")
        elif message.message_type == "shutdown":
            print(f"Node {self.node_id} received shutdown signal.")
            self.stop()
        else:
            print(f"Node {self.node_id}: Unknown message type {message.message_type}.")

    def critical_section(self):
        self.send_message(self.network, "central", "request_access")
    
    def real_critical_section(self):
        print(f"Node {self.node_id} is in critical section.")
        time.sleep(2)  # Simulujem praci
        print(f"Node {self.node_id}: Releasing access.")
        self.send_message(self.network, "central", "release_access")

    def run(self):
        while self.running:
            try:
                message = self.inbox.get(timeout=1)
                if message is None:  # Pokud je zpráva None, ukonči smyčku
                    break
                self.process_message(message)
            except queue.Empty:
                continue
        print(f"Node {self.node_id} thread has exited.")
                
class CentralCoordinator:
    def __init__(self, network):
        self.id = "central"
        self.request_queue = queue.Queue()
        self.lock = threading.Lock()
        self.running = False
        self.inbox = queue.Queue()
        self.thread = threading.Thread(target=self.run)
        self.network = network
        
        
    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.inbox.put(None)
        print(f"Central has been stopped.")

    def receive_message(self, message):
        self.inbox.put(message)

    def request_access(self, node_id):
        print(f"Node {node_id} requesting access to critical section.")
        self.request_queue.put(node_id)
        self.process_queue()
        
    def process_queue(self):
        if not self.lock.locked() and not self.request_queue.empty():
            next_node = self.request_queue.get()
            print(f"Central coordinator: Granting access to Node {next_node}.")
            self.lock.acquire()  # Zamknutí zámku
            self.send_message(self.network, next_node, "access_granted")
    
    def release_access(self, node_id):
        print(f"Node {node_id} released access to critical section.")
        self.lock.release()
        self.process_queue()
        
    def send_message(self,network, recipient_id, message_type, content=None):
        message = Message(sender_id=self.id, recipient_id=recipient_id, message_type=message_type, content=content)
        network.deliver_message(message)
    
    def process_message(self, message):
        if message.message_type == "request_access":
            self.request_access(message.sender_id)
        elif message.message_type == "release_access":
            self.release_access(message.sender_id)
        elif message.message_type == "shutdown":
            print(f"Central coordinator received shutdown signal.")
            self.stop()
        else:
            print(f"Central coordinator: Unknown message type {message.message_type}.")
        
    
    def run(self):
        while self.running:
            try:
                message = self.inbox.get(timeout=1)
                if message is None:  # Pokud je zpráva None, ukonč smyčku
                    break
                self.process_message(message)
            except queue.Empty:
                continue
        print(f"Central node thread has exited.")       
            
class Network:
    def __init__(self):
        self.id = 0
        self.nodes = {} 
        self.central = CentralCoordinator(self)
        self.central.start()
        self.network_inbox = queue.Queue()
        self.running = True
        
        self.network_thread = threading.Thread(target=self.run)
        self.network_thread.start()
              
    ########VOLANE UZIVATELEM########
    
    def stop(self):
    # Poslat zprávu všem uzlům, aby se vypnuly
        for node_id in list(self.nodes):  
            self.deliver_message(Message(sender_id=0, recipient_id=node_id, message_type="shutdown"))

        for node in self.nodes.values():
           node.thread.join()  # Počkáme, než se každý uzel skutečně vypne
           
        self.central.stop()
        self.central.thread.join()

        # Zastavit síť
        self.running = False
        self.network_thread.join()
        print("Network has been stopped.")
    
    def register_node(self, message):
        node_id = message.content["node_id"]
        name = message.content["name"]
        if node_id not in self.nodes:
            new_node = Node(node_id, name)
            new_node.network = self
            self.nodes[node_id] = new_node
            new_node.start()
            print(f"Node {node_id} ({name}) registered.")                    
        else:
            print(f"Node {node_id} already exists.")
     
########VOLANI ZPRAVY########   
    def deliver_message(self, message):
        if message.recipient_id == 0:
            self.network_inbox.put(message)
        elif message.recipient_id == "central":
            delay = random.uniform(0.1, 1.0)
            threading.Timer(delay, self.central.receive_message, args=[message]).start()
        elif message.recipient_id in self.nodes:
            delay = random.uniform(0.1, 1.0)
            threading.Timer(delay, self.nodes[message.recipient_id].receive_message, args=[message]).start()
        else:
            print(f"Message to unknown recipient {message.recipient_id} dropped.")

    def process_message(self, message):
        if message.message_type == "register_node":
            self.register_node(message)
        else:
            print(f"Unknown message type: {message.message_type}")
                           
###########ROZJETI SITĚ###########
    def run(self):
        while self.running:
            try:
                message = self.network_inbox.get(timeout=1)
                self.process_message(message)
            except queue.Empty:
                continue

if __name__ == "__main__":
    network = Network()
    
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 1, "name": "node1"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 2, "name": "node2"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 3, "name": "node3"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 4, "name": "node4"}))
    
    
    time.sleep(2)
    print()

    network.deliver_message(Message(sender_id="admin", recipient_id=1, message_type="critical_section"))
    network.deliver_message(Message(sender_id="admin", recipient_id=2, message_type="critical_section"))
    network.deliver_message(Message(sender_id="admin", recipient_id=3, message_type="critical_section"))
    network.deliver_message(Message(sender_id="admin", recipient_id=5, message_type="critical_section"))
    network.deliver_message(Message(sender_id="admin", recipient_id=4, message_type="critical_section"))


    time.sleep(15)

    # Ukončení sítě
    network.stop()
    
