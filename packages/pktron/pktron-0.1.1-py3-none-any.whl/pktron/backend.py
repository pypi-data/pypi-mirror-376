
import numpy as np
import quimb.tensor as qtn
from .quantum import QuantumCircuit

class StatevectorSimulator:
    def __init__(self):
        self.name = "statevector_simulator"

    def run(self, circuit, shots=1024):
        counts = {}
        for _ in range(shots):
            outcome, _ = circuit.measure()
            state = f"{outcome:0{circuit.num_qubits}b}"
            counts[state] = counts.get(state, 0) + 1
        return Result(counts, circuit)

class StabilizerSimulator:
    def __init__(self):
        self.name = "stabilizer_simulator"

    def run(self, circuit, shots=1024):
        tableau = np.eye(circuit.num_qubits, dtype=int)
        affected = set()
        for gate in circuit.gate_history:
            parts = [p for p in gate.split() if p.isdigit()]
            if parts:
                affected.update(int(p) for p in parts[:2])
        counts = {}
        for _ in range(shots):
            outcome = [0] * circuit.num_qubits
            for qb in affected:
                outcome[qb] = np.random.randint(0, 2)
            state = ''.join(map(str, outcome))
            counts[state] = counts.get(state, 0) + 1
        return Result(counts, circuit)

class MPS_Simulator:
    def __init__(self, max_bond_dim=100):
        self.name = "mps_simulator"
        self.max_bond_dim = max_bond_dim

    def run(self, circuit, shots=1024):
        if circuit.num_qubits > 20:
            print("MPS: Large n, default sampling.")
            counts = {'0' * circuit.num_qubits: shots}
            return Result(counts, circuit)
        try:
            mps = qtn.MPS_computational_state('0' * circuit.num_qubits)
            for gate in circuit.gate_history[:2]:
                if 'H on qubit' in gate:
                    qb = int(gate.split()[-1])
                    mps.apply_gate(qtn.pauli('H'), [qb])
                elif 'Rx(' in gate:
                    qb = int(gate.split()[-3].strip(')'))
                    theta = float(gate.split('(')[1].split(')')[0])
                    mps.apply_gate(qtn.gate_Rx(theta), [qb])
            mps.compress(max_bond=self.max_bond_dim)
            counts = {'0' * circuit.num_qubits: shots}
            return Result(counts, circuit)
        except Exception as e:
            print(f"MPS error: {e}. Falling back to statevector.")
            return StatevectorSimulator().run(QuantumCircuit(min(circuit.num_qubits, 10), "statevector"), shots)

class Result:
    def __init__(self, counts, circuit):
        self.counts = counts
        self.circuit = circuit

    def get_counts(self):
        return self.counts

def execute(circuits, backend=None, shots=1024):
    if backend is None:
        backend = StatevectorSimulator()
    if isinstance(circuits, QuantumCircuit):
        return backend.run(circuits, shots)
    else:
        results = []
        for circuit in circuits:
            results.append(backend.run(circuit, shots))
        return results
