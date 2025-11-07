# Hackathon-Opmobility
Simulated attack ON CAN

Overview
This project is a proof-of-concept (PoC) emulator for the Hussar Academy Hackathon: Secure Subsystems in Automotive (November 2025, Topic 1: Lightweight Authentication for LIN/CAN Probes). It simulates a CAN bus environment to demonstrate defenses against spoofing and tampering attacks on low-resource automotive probes (e.g., sensors sending data to ECUs).
Key Goals

Problem Addressed: Verify message authenticity/integrity on resource-constrained probes without heavy crypto, using CAN's built-in error mechanisms (active error frames, TEC counters).
Innovation: ID whitelisting + error-based invalidation for spoofing; burst detection for tampering countermeasures. Fits constraints: <1ms latency, zero added cost, bus-compatible.
Tech Stack: Pure Python 3 (no external libs) for quick prototyping. Extensible to hardware (Arduino/STM32).

This emulator models three entities:

Probe: Legitimate sensor sending periodic data.
Attacker: Simulates spoofing (ID impersonation) and tampering (data/CRC edits).
Bus/ECU: Shared medium with validation logic, error handling, and tamper burst detection.

Run it to see attacks rejected in real-time—perfect for hackathon demos!
Features

Attack Simulation: Spoofing (fake IDs/data) and tampering (bit-flips with CRC recompute).
Defenses:

Whitelist filtering: Rejects non-matching IDs.
Active error frames: Aborts bad messages, increments TEC.
Tamper burst detection: Counters error floods (>8/sec) to force attacker passive/Bus Off.

Metrics: Tracks TEC, validation rates; logs for analysis.
Realism: Threaded for concurrency; simple CRC for integrity checks.
Extensibility: Easy to add LIN mode, noise, or port to hardware.
