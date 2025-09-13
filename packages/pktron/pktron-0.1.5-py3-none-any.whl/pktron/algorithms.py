
import numpy as np
from .gates import h, rx, ry, cnot, cz, s, toffoli, t, x
from .quantum import QuantumCircuit
from .backend import execute, StatevectorSimulator

def quantum_flip(circuit):
    h(circuit, 0)
    if circuit.num_qubits > 1:
        cnot(circuit, 0, 1)
    rx(circuit, 0, np.pi/4)
    circuit.gate_history.append("Quantum Flip")

def super_quantum_dance(circuit):
    h(circuit, 0)
    if circuit.num_qubits > 1:
        ry(circuit, 1, np.pi/2)
        cnot(circuit, 0, 1)
    if circuit.num_qubits > 2:
        toffoli(circuit, 0, 1, 2)
    t(circuit, 0)
    circuit.gate_history.append("Super Quantum Dance")

def quantum_treasure_hunt(circuit):
    target_state = 2**circuit.num_qubits - 1
    h(circuit, 0)
    if circuit.num_qubits > 1:
        cnot(circuit, 0, 1)
        ry(circuit, 1, np.random.uniform(0, np.pi))
    rx(circuit, 0, np.random.uniform(0, np.pi))
    outcome, probs = circuit.measure()
    score = probs[target_state] * 100
    circuit.gate_history.append(f"Quantum Treasure Hunt (Score: {score:.1f})")
    return score

def quantum_magic_spin(circuit):
    target_state = 0
    rx(circuit, 0, np.random.uniform(0, 2*np.pi))
    if circuit.num_qubits > 1:
        ry(circuit, 1, np.random.uniform(0, np.pi))
        cz(circuit, 0, 1)
    s(circuit, 0)
    outcome, probs = circuit.measure()
    score = probs[target_state] * 100
    circuit.gate_history.append(f"Quantum Magic Spin (Score: {score:.1f})")
    return score

def bb84_qkd(num_qubits, eve_intercept_prob=0.5, seed=None):
    if seed is not None:
        np.random.seed(seed)
    
    qc = QuantumCircuit(num_qubits, "statevector")
    
    alice_bits = np.random.randint(0, 2, num_qubits)
    alice_bases = np.random.randint(0, 2, num_qubits)
    
    eve_intercepts = np.random.choice([0, 1], size=num_qubits, p=[1-eve_intercept_prob, eve_intercept_prob])
    eve_bases = np.random.randint(0, 2, num_qubits)
    
    bob_bases = np.random.randint(0, 2, num_qubits)
    
    for i in range(num_qubits):
        if alice_bits[i] == 1:
            x(qc, i)
        if alice_bases[i] == 1:
            h(qc, i)
    
    for i in range(num_qubits):
        if eve_intercepts[i]:
            if eve_bases[i] == 1:
                h(qc, i)
            # Simulate Eve's measurement and re-preparation (random bit)
            x(qc, i) if np.random.randint(0, 2) == 1 else None
            if eve_bases[i] == 1:
                h(qc, i)
    
    for i in range(num_qubits):
        if bob_bases[i] == 1:
            h(qc, i)
    
    outcome, probs = qc.measure()
    measured_bits = [int(b) for b in format(outcome, f'0{qc.num_qubits}b')]
    
    alice_key = []
    bob_key = []
    for i in range(num_qubits):
        if alice_bases[i] == bob_bases[i]:
            alice_key.append(alice_bits[i])
            bob_key.append(measured_bits[i])
    
    error_count = sum(a != b for a, b in zip(alice_key, bob_key))
    error_rate = error_count / len(alice_key) if alice_key else 0.0
    
    eve_detected = error_rate > 0.25
    
    qc.gate_history.append(f"BB84 QKD (Error rate: {error_rate:.2f}, Eve detected: {eve_detected})")
    
    return {
        "alice_key": alice_key,
        "bob_key": bob_key,
        "error_rate": error_rate,
        "eve_detected": eve_detected,
        "alice_bases": alice_bases.tolist(),
        "bob_bases": bob_bases.tolist(),
        "eve_intercepts": eve_intercepts.tolist(),
        "circuit": qc
    }
