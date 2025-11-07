import time
import threading
import random

class CANMessage:
    def __init__(self, id, data, sender):
        self.id = id
        self.data = data
        self.sender = sender
        self.timestamp = time.time()
    
    def __str__(self):
        return f"ID: {self.id:03X}, Data: {self.data}, Sender: {self.sender}"

class CANBus:
    def __init__(self):
        self.messages = []
        self.lock = threading.Lock()
    
    def send(self, msg):
        with self.lock:
            self.messages.append(msg)
            print(f"[BUS] {msg} sent at {msg.timestamp:.3f}")
    
    def recv(self):
        with self.lock:
            if self.messages:
                return self.messages.pop(0)
        return None
    
    def get_traffic(self):
        with self.lock:
            return len(self.messages)

class Probe:
    def __init__(self, bus, node_id=0x123):
        self.bus = bus
        self.node_id = node_id
        self.legit_data = [0x01, 0x02, 0x03]
    
    def send_legit(self):
        msg = CANMessage(self.node_id, self.legit_data[:], "Probe")
        self.bus.send(msg)
        print("[PROBE] Sent legitimate message.")

class Attacker:
    def __init__(self, bus, target_id=0x123):
        self.bus = bus
        self.target_id = target_id
    
    def spoof(self):
        tampered_data = [0x99, 0x99, 0x99]  # Spoofed data
        msg = CANMessage(self.target_id, tampered_data, "Attacker")
        self.bus.send(msg)
        print("[ATTACKER] Sent spoofed message.")
    
    def tamper(self):
        # Simulate tampering: but since bus is shared, just send altered
        tampered_data = [0x01, 0xFF, 0x03]  # Partial tamper
        msg = CANMessage(self.target_id, tampered_data, "Attacker")
        self.bus.send(msg)
        print("[ATTACKER] Attempted tamper.")

# Whitelist countermeasure simulation
def check_whitelist(msg, whitelist=[0x123]):
    if msg.id not in whitelist:
        print("[COUNTER] Rejected: Invalid ID")
        return False
    expected_data = [0x01, 0x02, 0x03]
    if msg.data != expected_data:
        print("[COUNTER] Detected anomaly in data - would trigger error frame!")
        return False
    print("[COUNTER] Message validated.")
    return True

# Emulation setup
bus = CANBus()
probe = Probe(bus)
attacker = Attacker(bus)

# Simulate sequence in threads for realism
def run_sequence():
    # Legit send
    probe.send_legit()
    time.sleep(0.1)
    
    # Receive and check
    msg = bus.recv()
    if msg:
        check_whitelist(msg)
    
    # Attack: Spoof
    attacker.spoof()
    time.sleep(0.1)
    
    # Receive and check
    msg = bus.recv()
    if msg:
        check_whitelist(msg)
    
    # Attack: Tamper
    attacker.tamper()
    time.sleep(0.1)
    
    # Receive and check
    msg = bus.recv()
    if msg:
        check_whitelist(msg)

# Run
print("=== CAN Bus Emulation: Probe + Attacker + Bus ===")
run_sequence()
print(f"Total messages on bus: {bus.get_traffic()}")
