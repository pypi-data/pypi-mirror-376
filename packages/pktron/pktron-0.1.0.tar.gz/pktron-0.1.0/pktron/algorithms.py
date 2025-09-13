
import numpy as np
from .gates import h, rx, ry, cnot, cz, s, toffoli, t

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
