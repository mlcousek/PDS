import threading
import queue
import time
import random

FOLLOWER = 0
CANDIDATE = 1
LEADER = 2

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
               
        #RAFT
        self.state = FOLLOWER
        self.term = 0
        self.votes_received = 0
        self.vote_granted = False
        self.election_timeout = time.time() + random.uniform(3, 6)
                
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
        if message.message_type == "request_vote":
            self.request_vote(message.content.get("candidate"), message.content.get("term"))
            
        elif message.message_type == "heartbeat":
            self.receive_heartbeat(message.content.get("self"))
        
        elif message.message_type == "receive_vote":
            self.votes_received += 1 
            print(f"Node {message.content.get("voter").node_id} voted for Node {self.node_id} ({self.votes_received} votes) in term {message.content.get("term")}.")
            
        elif message.message_type == "restart": 
            self.state = FOLLOWER
            self.term = 0
            self.votes_received = 0
            self.vote_granted = False
            self.election_timeout = time.time() + random.uniform(3, 5)
            print(f"Node {self.node_id} has been restarted.")
        
        elif message.message_type == "shutdown":
            print(f"Node {self.node_id} received shutdown signal.")
            self.stop()
        else:
            print(f"Node {self.node_id}: Unknown message type {message.message_type}.")

    ########RAFT FUNKCE######## 
    # Raft follower logika
    def run_follower(self):
        if time.time() > self.election_timeout:
            self.start_election()
    
    # Raft candidate logika
    def run_candidate(self):
        self.term += 1
        self.votes_received = 1  # Hlasuji pro sebe
        self.vote_granted = True
        print(f"Node {self.node_id} is starting election for term {self.term}.")
        
        # Požádá ostatní uzly o hlasy
        if self.network:
            for node in self.network.nodes.values():
                if node.node_id != self.node_id:
                    self.send_message(self.network, node.node_id, "request_vote", {"candidate": self, "term": self.term})
                    
        # Čekání na výsledek hlasování
        start_time = time.time()
        while time.time() - start_time < 4:  
            if self.votes_received > len(self.network.nodes) // 2:
                self.state = LEADER
                print(f"Node {self.node_id} has been elected leader for term {self.term}.")
                break
            try:
                message = self.inbox.get(timeout=0.3)  # Vyčkej na zprávu max 0.3 sekundy
                if message:
                  self.process_message(message)  # Zpracuj zprávu
            except queue.Empty:
             pass  # Pokud není žádná zpráva, pokračuj v cyklu
        
        if self.state != LEADER:
            self.state = FOLLOWER
            self.vote_granted = False
    
    # Raft leader logika
    def run_leader(self):
        print(f"Node {self.node_id} is the leader, maintaining the cluster.")
        time.sleep(1)  # Posílá heartbeat každou sekundu
        if self.network:
            for node in self.network.nodes.values():
                if node.node_id != self.node_id:
                    self.send_message(self.network, node.node_id, "heartbeat", {"self": self})                   
    
    def start_election(self):
        self.state = CANDIDATE
        self.election_timeout = time.time() + random.uniform(3, 5)

    def request_vote(self, candidate, current_term): 
        if  current_term > self.term:
            self.term = current_term
            self.state = FOLLOWER
            self.election_timeout = time.time() + random.uniform(3, 5)
            self.vote_granted = True
            self.send_message(self.network, candidate.node_id, "receive_vote", {"voter": self, "term": self.term})
        elif current_term == self.term and not self.vote_granted:
            self.vote_granted = True
            self.send_message(self.network, candidate.node_id, "receive_vote", {"voter": self, "term": self.term})
        

    def receive_heartbeat(self, leader):
        self.state = FOLLOWER
        self.vote_granted = False
        self.election_timeout = time.time() + random.uniform(3, 5)
        print(f"Node {self.node_id} received heartbeat from Leader {leader.node_id}.")

    def run(self):
        while self.running:
            if self.state == FOLLOWER:
                self.run_follower()
            elif self.state == CANDIDATE:
                self.run_candidate()
            elif self.state == LEADER:
                self.run_leader()
                
            try:
                message = self.inbox.get(timeout=1)
                if message is None:  # Pokud je zpráva None, ukonči smyčku
                    break
                self.process_message(message)
                               
            except queue.Empty:
                continue
        print(f"Node {self.node_id} thread has exited.")
                    
class Network:
    def __init__(self):
        self.id = 0
        self.nodes = {} 
        self.node_hashes = set() # Množina pro unikátní kombinace (node_id, node_hash)
        self.network_inbox = queue.Queue()
        self.running = True
        
        self.network_thread = threading.Thread(target=self.run)
        self.network_thread.start()
              
    ########VOLANE UZIVATELEM########
    def stop(self):
        for node_id in list(self.nodes):  
            self.deliver_message(Message(sender_id=0, recipient_id=node_id, message_type="shutdown"))
            
        for node in self.nodes.values():
           node.thread.join()  # Počkáme, než se každý uzel skutečně vypne

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
        elif message.recipient_id in self.nodes:
            delay = random.uniform(0.1, 1)
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
    
    """
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 5, "name": "node5"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 6, "name": "node6"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 7, "name": "node7"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 8, "name": "node8"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 9, "name": "node9"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 10, "name": "node10"}))
    #"""
    time.sleep(20)
    

    #RAFT TESTY = PUSTIT RAFT V RUN funkci nodu
    network.deliver_message(Message(sender_id="admin", recipient_id=4, message_type="restart")) 
    time.sleep(40)
    
    #time.sleep(10)
    
    # Ukončení sítě
    network.stop()