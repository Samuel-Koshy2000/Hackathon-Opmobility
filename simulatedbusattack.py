import time
import threading

class CANMessage:
    def __init__(self, id, data, sender, crc=None):
        self.id = id
        self.data = data  # List of bytes
        self.sender = sender
        self.crc = crc or self.compute_crc()  # Auto-CRC for integrity
        self.timestamp = time.time()
    
    def compute_crc(self):  # Simple 8-bit CRC sim (real CAN is 15-bit poly)
        crc = 0xFF
        for byte in self.data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31  # XOR poly
                else:
                    crc <<= 1
                crc &= 0xFF
        return crc
    
    def is_tampered(self, original_data):  # Check for edits
        return self.data != original_data or self.crc != self.compute_crc()
    
    def __str__(self):
        return f"ID: {self.id:03X}, Data: {self.data}, CRC: {self.crc:02X}, Sender: {self.sender}"

class CANBus:
    def __init__(self):
        self.messages = []  # Queue of pending frames
        self.lock = threading.Lock()  # Thread-safe
        self.error_history = []  # For tamper detection (bursts)
        self.tec = {}  # Dict to track TEC per sender
    
    def send(self, msg, is_error=False):  # is_error: Sim active error frame
        with self.lock:
            if is_error:
                print(f"[BUS] ACTIVE ERROR FRAME! Aborting {msg} - TEC++ for {msg.sender}")
                self.error_history.append(time.time())  # Log burst
                sender_tec = self.tec.get(msg.sender, 0) + 8
                self.tec[msg.sender] = sender_tec
                print(f"[BUS] {msg.sender} TEC now: {sender_tec}")
                if sender_tec > 127:
                    print(f"[BUS] {msg.sender} entering ERROR PASSIVE!")
                if sender_tec > 255:
                    print(f"[BUS] {msg.sender} BUS OFF!")
                return  # Drop the bad msg
            self.messages.append(msg)
            print(f"[BUS] {msg} sent at {msg.timestamp:.3f}s")
    
    def recv(self):  # Next node gets it
        with self.lock:
            if self.messages:
                return self.messages.pop(0)
        return None
    
    def check_tamper_burst(self):  # Your counter: Spot error storms
        now = time.time()
        recent_errors = [t for t in self.error_history if now - t < 1.0]  # 1s window
        if len(recent_errors) > 8:  # Threshold for "attack"
            print("[BUS] TAMPER BURST DETECTED! Counter-flooding attacker.")
            self.error_history = []  # Reset
            return True  # Trigger global error
        return False

class Node:
    def __init__(self, bus, node_id):
        self.bus = bus
        self.node_id = node_id
        self.is_passive = False
        self.whitelist = [node_id]  # Your spoof fix: Only trust my ID
        self.expected_data = [0x01, 0x02, 0x03]  # Legit sensor data
    
    def validate_msg(self, msg):  # Whitelist + tamper check
        if msg.id not in self.whitelist:
            print(f"[ECU] SPOOF DETECTED! Rejecting ID {msg.id}")
            self.bus.send(msg, is_error=True)
            return False
        if msg.is_tampered(self.expected_data):
            print(f"[ECU] TAMPER DETECTED! Rejecting (data/CRC mismatch)")
            self.bus.send(msg, is_error=True)
            return False
        print(f"[ECU] VALID: Accepted {msg}")
        return True

class Probe(Node):  # Legit sensor
    def __init__(self, bus, node_id=0x123):
        super().__init__(bus, node_id)
    
    def send_legit(self, data=None):
        data = data or self.expected_data
        msg = CANMessage(self.node_id, data[:], "Probe")
        self.bus.send(msg)

class Attacker(Node):  # Bad guy
    def __init__(self, bus, target_id=0x123):
        super().__init__(bus, 0x999)  # Own ID, but spoofs target
        self.target_id = target_id
    
    def spoof_attack(self):
        fake_data = [0x99, 0x99, 0x99]
        msg = CANMessage(self.target_id, fake_data, "Attacker")
        self.bus.send(msg)
    
    def tamper_attack(self):
        base_data = [0x01, 0x02, 0x03]
        tampered = base_data.copy()
        tampered[1] = 0xFF  # Flip middle byte
        msg = CANMessage(self.target_id, tampered, "Attacker")
        self.bus.send(msg)
    
    def authentic_attack(self):  # "Perfect" spoof/replay - exact copy
        msg = CANMessage(self.target_id, self.expected_data[:], "Attacker")
        self.bus.send(msg)

# Scenario Runner
def run_scenarios():
    bus = CANBus()
    probe = Probe(bus)
    attacker = Attacker(bus)
    ecu = Node(bus, 0x123)  # ECU as validator
    
    scenarios = [
        ("=== SCENARIO 1: LEGITIMATE MESSAGE (PASSES) ===", lambda: probe.send_legit()),
        ("=== SCENARIO 2: SPOOF ATTACK (DETECTED, REJECTED) ===", lambda: attacker.spoof_attack()),
        ("=== SCENARIO 3: TAMPER ATTACK (DETECTED, REJECTED) ===", lambda: attacker.tamper_attack()),
        ("=== SCENARIO 4: ATTACK PASSES AS AUTHENTIC (FALSE NEGATIVE - Exact copy) ===", lambda: attacker.authentic_attack()),
        ("=== SCENARIO 5: LEGIT MESSAGE FLAWED AS ATTACK (FALSE POSITIVE - Noise in data) ===", lambda: probe.send_legit([0x01, 0x02, 0x04])),
    ]
    
    for title, action in scenarios:
        print(title)
        action()
        time.sleep(0.1)  # Tiny delay for sequencing
        msg = bus.recv()
        if msg:
            ecu.validate_msg(msg)
        bus.check_tamper_burst()  # Check after each
        time.sleep(0.5)  # Pause between scenarios
    
    print("\n=== END DEMO ===")

if __name__ == "__main__":
    print("CAN Bus Security Scenarios Demo\n")
    run_scenarios()
