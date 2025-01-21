import threading
import queue
import time
import random
import mmh3

class Message:
    def __init__(self, sender_id, recipient_id, message_type, content=None):
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.message_type = message_type
        self.content = content
        
class Node:
    def __init__(self, node_id, name):
        self.node_id = node_id
        self.name = name
        self.inbox = queue.Queue()
        self.running = False
        self.network = None
        
        self.hash_value = mmh3.hash(name, 0, False)
        self.resources = {}
        self.previous = None
        self.next = None
        self.fingerTable = {}
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
        if message.message_type == "add_resource":
            self.resources[message.content["hashValueResource"]] = message.content["name"]
            print(f"Node {self.node_id}: Resource {message.content['name']} added.")
        #HASHRING    
        elif message.message_type == "find_in_hashringNODE":
            self.findInHashRingNODE(message.content["name"])
            
        elif message.message_type == "find_in_hashring":
            self.findInHashRing(message.content["hash"], message.content["first"], message.content["steps"], message.content["name"])
            
        elif message.message_type == "found_in_hashring":
            print(f"Node {self.name}: Resource with name {message.content['name']} found in hashring on server {message.content['server_name']} in {message.content['steps']} steps.")
            
        elif message.message_type == "not_found_in_hashring":
            print(f"Node {self.node_id}: Resource with name {message.content['name']} not found in hashring in {message.content['steps']} steps.")
        #CHORD
        elif message.message_type == "find_in_chordNODE":
            self.findInChordNODE(message.content["name"])
            
        elif message.message_type == "find_in_chord":
            self.findInChord(message.content["hash"], message.content["first"], message.content["steps"], message.content["name"], message.content["prev_id"])    
        
        elif message.message_type == "found_in_chord":
            print(f"Node {self.name}: Resource with name {message.content['name']} found in chord on server {message.content['server_name']} in {message.content['steps']} steps.")
        
        elif message.message_type == "not_found_in_chord":
            print(f"Node {self.node_id}: Resource with name {message.content['name']} not found in chord in {message.content['steps']} steps.")
        
        elif message.message_type == "shutdown":
            print(f"Node {self.node_id} received shutdown signal.")
            self.stop()
        else:
            print(f"Node {self.node_id}: Unknown message type {message.message_type}.")

    def findInHashRingNODE(self, name):
        hashValue = mmh3.hash(name, 0, False)
        steps = 0 
        if self.network.legalRange(hashValue):
            self.findInHashRing(hashValue, self.node_id, steps, name)

    def findInHashRing(self, hashValue, first, steps, name):
        if self.network.legalRange(hashValue):
            steps = steps + 1
            if hashValue in self.resources:
                self.send_message(self.network, first, "found_in_hashring", {"steps": steps, "name": name,"server_name": self.name})
                return
            if self.network.distance(self.hash_value, hashValue) > self.network.distance(self.next.hash_value, hashValue):
                self.send_message(self.network, self.next.node_id, "find_in_hashring", {"hash": hashValue, "first": first, "steps": steps, "name": name})
                return
            else:
                if hashValue not in self.next.resources:
                    self.send_message(self.network, first, "not_found_in_hashring", {"steps": steps + 1, "name": name})
                    return
                else:
                    self.send_message(self.network, first, "found_in_hashring", {"steps": steps + 1, "name": name, "server_name": self.next.name})
                    return
        self.send_message(self.network, first, "not_found_in_hashring", {"steps": steps, "name": name})
        return
    
    def findInChordNODE(self, name):
        hashValue = mmh3.hash(name, 0, False)
        steps = 0 
        if self.network.legalRange(hashValue):
            self.findInChord(hashValue, self.node_id, steps, name, None)
    
    def findInChord(self, hashValue, first, steps, name, prev_id):
        if self.network.legalRange(hashValue):
            steps = steps + 1
            if hashValue in self.resources:
                self.send_message(self.network, first, "found_in_chord", {"steps": steps, "name": name,"server_name": self.name})
                return
                    
            if self.hash_value == hashValue:
                if hashValue not in self.resources:
                #    self.send_message(self.network, first, "found_in_chord", {"steps": steps, "name": name, "server_name": self.name})
                #    return
                #else:
                    self.send_message(self.network, first, "not_found_in_chord", {"steps": steps, "name": name})
                    return
            
            closest_finger = self
            for i in range(self.network.k - 1, -1, -1):  # procházíme od nejvzdálenějšího
                if self.network.distance(self.fingerTable[i].hash_value, hashValue) < self.network.distance(closest_finger.hash_value, hashValue):
                    closest_finger = self.fingerTable[i]
            
            if hashValue in self.next.resources:
                self.send_message(self.network, first, "found_in_chord", {"steps": steps + 1, "name": name, "server_name": self.next.name})
                return
            
            if prev_id:
                if prev_id == self.node_id:
                    self.send_message(self.network, first, "not_found_in_chord", {"steps": steps, "name": name})
                    return
            
            self.send_message(self.network, closest_finger.node_id, "find_in_chord", {"hash": hashValue, "first": first, "steps": steps, "name": name, "prev_id": self.node_id})
            return
                       
        self.send_message(self.network, first, "not_found_in_chord", {"steps": steps, "name": name})
        return
            
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
                
#Vím je to naprd, když to přidávání a ty finger tables jsou centrálně udělané a, že to trochu postrádá smysl
#ale řekl jsem si, že předělám centralizované řešení, co jsme dělali do algoritmu a vím, že to byla chyba a beru to jako poučení do příště a doufám, že to bude takto stačit
#protože to vyhledávání jak v hashringu nebo v chordu je už čistě distribuované 
                           
class Network:
    def __init__(self, k):
        self.id = 0
        self.nodes = {} 
        self.node_hashes = set() # Množina pro unikátní kombinace (node_id, node_hash)
        self.network_inbox = queue.Queue()
        self.running = True
        
        self.head = None
        self.k = k
        self.min = 0
        self.max = 2**k - 1
        
        self.network_thread = threading.Thread(target=self.run)
        self.network_thread.start()    
    ########POMOCNE FUNKCE########     
    def legalRange(self, hashValue):
        return self.min <= hashValue <= self.max

    def distance(self, a, b):
        if a == b:
            return 0
        elif a < b:
            return b - a
        else:
            return (2**self.k) + (b - a)
    
    def lookupNode(self, hash_value): #TENTO LOOKUP NODE SE POUZIVA JEN PRO VNITRNI FUNKCE, ALE UZIVATEL UZ VOLA FUNKCE CO FUNGUJU DISTRIBUTIVNE
        if self.legalRange(hash_value):
            temp = self.head
            if temp is None:
                return None
            else:
                while(self.distance(temp.hash_value, hash_value) >
                        self.distance(temp.next.hash_value, hash_value)):
                    temp = temp.next
                if temp.hash_value == hash_value:
                    return temp
                return temp.next
    
    def moveResources(self, dest, orig, deleteTrue):
        delete_list = []
        for i, j in orig.resources.items():
            if (self.distance(i, dest.hash_value) < self.distance(i, orig.hash_value) or deleteTrue):
                dest.resources[i] = j
                delete_list.append(i)
        for i in delete_list:
            del orig.resources[i]
            
    def buildFingerTables(self):
        if self.head is None:
            return
        temp = self.head
        while True:
            for i in range(self.k):  
                finger_hash = (temp.hash_value + 2**i) % (2**self.k)
                successor = self.lookupNode(finger_hash)
                temp.fingerTable[i] = successor
            temp = temp.next
            if temp == self.head:
                break             
    ########VOLANE UZIVATELEM########
    
    def stop(self):
    # Poslat zprávu všem uzlům, aby se vypnuly
        for node_id in list(self.nodes):  
            self.remove_node(name=self.nodes[node_id].name, stop=True) 
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
        node_hash =  mmh3.hash(name, 0, False)
        if node_id not in self.nodes:
            if (node_id, node_hash) not in self.node_hashes:
                
                new_node = Node(node_id, name)
                new_node.network = self
                self.nodes[node_id] = new_node
                self.node_hashes.add((node_id, node_hash))
                new_node.start()
                
                if self.head is None:
                    new_node.next = new_node
                    new_node.previous = new_node
                    self.head = new_node
                else:
                    temp = self.lookupNode(new_node.hash_value)
                    new_node.next = temp
                    new_node.previous = temp.previous
                    new_node.previous.next = new_node
                    new_node.next.previous = new_node
                    
                    self.moveResources(new_node, new_node.next, False)

                    if new_node.hash_value < self.head.hash_value:
                        self.head = new_node
                self.buildFingerTables()
                print(f"Node with ID {node_id} and hash {node_hash} added.")
            
            else:
                print(f"Node with ID {node_id} and hash {node_hash} already exists!")            
        else:
            print(f"Node {node_id} already exists.")

    def remove_node(self, name, stop=False):
        hashValue =  mmh3.hash(name, 0, False)
        temp = self.lookupNode(hashValue)
        if temp is not None:
            if temp.hash_value == hashValue:
                self.moveResources(temp.next, temp, True)
                temp.previous.next = temp.next
                temp.next.previous = temp.previous
                if self.head.hash_value == hashValue:
                    if self.head == self.head.next:
                        self.head = None
                    else:
                        self.head = temp.next
                self.buildFingerTables()
                self.deliver_message(Message(sender_id=0, recipient_id=temp.node_id, message_type="shutdown"))
                temp.thread.join() 
                if not stop:
                    self.node_hashes.remove((temp.node_id, temp.hash_value))
                    self.nodes.pop(temp.node_id)
                print(f"{temp.name} removed.")
     
    def addResource(self, name):
        if self.head is None:
            print("No nodes in the network")
        else:
            hashValueResource = mmh3.hash(name, 0, False)
            if self.legalRange(hashValueResource):
                target_node = self.lookupNode(hashValueResource)
                if target_node is not None:
                    self.send_message(self, target_node.node_id, "add_resource", {"hashValueResource": hashValueResource, "name": name})

    def lookupNodeWithSteps(self, name):
        hashValue = mmh3.hash(name, 0, False)
        steps = 0  
        if self.legalRange(hashValue):
            temp = self.head
            if temp is None:
                print(f"Lookup in hashring: {name} is not in network (in {steps} steps).")
                return  
            else:
                self.send_message(self, temp.node_id, "find_in_hashring", {"hash": hashValue, "first": 0, "steps": steps, "name": name})
 
    # ChordLookupWithSteps 
    def chordLookupWithSteps(self, name):
        hashValue = mmh3.hash(name, 0, False)
        steps = 0  
        if self.head is None:
            print(f"Lookup in chord: {name} is not in network (in {steps} steps).")
            return   
        temp = self.head
        self.send_message(self, temp.node_id, "find_in_chord", {"hash": hashValue, "first": 0, "steps": steps, "name": name, "prev_id": None})

########VOLANI ZPRAVY########
    
    def deliver_message(self, message):
        if message.recipient_id == 0:
            self.network_inbox.put(message)
        elif message.recipient_id in self.nodes:
            delay = random.uniform(0.1, 1.0)
            threading.Timer(delay, self.nodes[message.recipient_id].receive_message, args=[message]).start()
        else:
            print(f"Message to unknown recipient {message.recipient_id} dropped.")

    def send_message(self,network, recipient_id, message_type, content=None):
        message = Message(sender_id=self.id, recipient_id=recipient_id, message_type=message_type, content=content)
        self.deliver_message(message)

    def process_message(self, message):
        if message.message_type == "register_node":
            self.register_node(message)
        elif message.message_type == "remove_node":
            self.remove_node(message.content["name"])
        elif message.message_type == "add_resource":
            self.addResource(message.content["name"])
        elif message.message_type == "find_in_hashring":
            self.lookupNodeWithSteps(message.content["name"])
        elif message.message_type == "found_in_hashring":
            print(f"Network: Resource with name {message.content['name']} found in hashring on server {message.content['server_name']} in {message.content['steps']} steps.")
        elif message.message_type == "not_found_in_hashring":
            print(f"Network: Resource with name {message.content['name']} not found in hashring in {message.content['steps']} steps.")
        elif message.message_type == "find_in_chord":
            self.chordLookupWithSteps(message.content["name"])
        elif message.message_type == "found_in_chord":
            print(f"Network: Resource with name {message.content['name']} found in chord on server {message.content['server_name']} in {message.content['steps']} steps.")
        elif message.message_type == "not_found_in_chord":
            print(f"Network: Resource with name {message.content['name']} not found in chord in {message.content['steps']} steps.")
        elif message.message_type == "print_hashring":
            self.printHashRing()
        else:
            print(f"Unknown message type: {message.message_type}")
               
    def printHashRing(self):
        print("*****")
        print("Printing the hashring in clockwise order:")
        temp = self.head
        if self.head is None:
            print("Empty hashring")
        else:
            while(True):
                print(f"Node: {temp.name} (hash {temp.hash_value}), Resources:", end=" ")

                if not bool(temp.resources):
                    print("Empty", end="")
                else:
                    for resource_hash, resource_name in temp.resources.items():
                        print(f"{resource_name} (hash {resource_hash})", end=" ")

                temp = temp.next
                print(" ")
                if (temp == self.head):
                    break
        print("*****")
        
                    
###########ROZJETI SITĚ###########
    def run(self):
        while self.running:
            try:
                message = self.network_inbox.get(timeout=1)
                self.process_message(message)
            except queue.Empty:
                continue

if __name__ == "__main__":
    network = Network(32)
    
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 1, "name": "node1"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 2, "name": "node2"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 3, "name": "node3"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 4, "name": "node4"}))
    
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 5, "name": "server"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 6, "name": "pecky"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 7, "name": "rakety"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 8, "name": "node99"}))
    
    time.sleep(2)

    #"""
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="add_resource", content={"name": "resource1"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="add_resource", content={"name": "pecky"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="add_resource", content={"name": "server?fake"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="add_resource", content={"name": "random"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="add_resource", content={"name": "1"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="add_resource", content={"name": "2"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="add_resource", content={"name": "server?fake2"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="add_resource", content={"name": "random"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="add_resource", content={"name": "resource10"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="add_resource", content={"name": "resource20"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="add_resource", content={"name": "1"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="add_resource", content={"name": "2"}))


    time.sleep(5)

    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="print_hashring"))
    

    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 9, "name": "server1"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 10, "name": "pecky1"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 11, "name": "rakety1"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="register_node", content={"node_id": 8, "name": "node991"}))
    
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="remove_node", content={"name": "node2"}))


    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="find_in_hashring", content={"name": "pecky"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="find_in_hashring", content={"name": "resource10000"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=1, message_type="find_in_hashringNODE", content={"name": "resource1"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=1, message_type="find_in_hashringNODE", content={"name": "resource1000"}))
    
    network.deliver_message(Message(sender_id="admin", recipient_id=1, message_type="find_in_chordNODE", content={"name": "resource1"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="find_in_chord", content={"name": "resource1", "prev_id": None}))

    network.deliver_message(Message(sender_id="admin", recipient_id=1, message_type="find_in_chordNODE", content={"name": "pecky"}))
    network.deliver_message(Message(sender_id="admin", recipient_id=0, message_type="find_in_chord", content={"name": "pecky", "prev_id": None}))

    time.sleep(10)
    # Ukončení sítě
    network.stop()
   
