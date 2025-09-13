
import numpy as np

class QuantumCircuit:
    def __init__(self, num_qubits, backend_type="statevector"):
        self.num_qubits = num_qubits
        self.backend_type = backend_type.lower()
        self._state = None
        self.gate_history = []

    def _allocate_state(self):
        if self._state is None:
            self._state = np.zeros(2**self.num_qubits, dtype=complex)
            self._state[0] = 1.0

    def get_state(self):
        if self.backend_type == "statevector":
            self._allocate_state()
            return self._state
        raise ValueError(f"get_state requires statevector backend, got {self.backend_type}")

    def normalize(self):
        if self.backend_type != "statevector" or self._state is None:
            return
        norm = np.sqrt(np.sum(np.abs(self._state)**2))
        if norm > 0:
            self._state /= norm

    def _apply_single_qubit_gate(self, gate, qubit):
        if qubit >= self.num_qubits:
            raise ValueError("Bad qubit number!")
        if self.backend_type == "statevector":
            self._allocate_state()
            full_gate = 1.0
            for i in range(self.num_qubits):
                if i == qubit:
                    full_gate = np.kron(full_gate, gate)
                else:
                    full_gate = np.kron(full_gate, np.eye(2))
            self._state = np.dot(full_gate, self._state)
            self.normalize()
        # For non-statevector, do nothing (history only)

    def _apply_two_qubit_gate(self, gate, qubit1, qubit2):
        if qubit1 == qubit2 or qubit1 >= self.num_qubits or qubit2 >= self.num_qubits:
            raise ValueError("Bad qubit numbers!")
        if self.backend_type == "statevector":
            self._allocate_state()
            qubits = sorted([qubit1, qubit2])
            full_gate = 1.0
            i = 0
            while i < self.num_qubits:
                if i == qubits[0]:
                    two_qubit_full = gate
                    for j in range(1, qubits[1] - qubits[0]):
                        two_qubit_full = np.kron(np.eye(2), two_qubit_full)
                    full_gate = np.kron(full_gate, two_qubit_full)
                    i = qubits[1] + 1
                else:
                    full_gate = np.kron(full_gate, np.eye(2))
                    i += 1
            self._state = np.dot(full_gate, self._state)
            self.normalize()
        # For non-statevector, do nothing

    def _apply_three_qubit_gate(self, gate, qubit1, qubit2, qubit3):
        if len(set([qubit1, qubit2, qubit3])) != 3 or max(qubit1, qubit2, qubit3) >= self.num_qubits:
            raise ValueError("Bad qubit numbers!")
        if self.backend_type == "statevector":
            self._allocate_state()
            qubits = sorted([qubit1, qubit2, qubit3])
            full_gate = 1.0
            i = 0
            while i < self.num_qubits:
                if i == qubits[0]:
                    three_qubit_full = gate
                    for j in range(1, qubits[2] - qubits[0]):
                        three_qubit_full = np.kron(np.eye(2), three_qubit_full)
                    full_gate = np.kron(full_gate, three_qubit_full)
                    i = qubits[2] + 1
                else:
                    full_gate = np.kron(full_gate, np.eye(2))
                    i += 1
            self._state = np.dot(full_gate, self._state)
            self.normalize()
        # For non-statevector, do nothing

    def measure(self):
        if self.backend_type != "statevector":
            raise ValueError(f"Measure requires statevector backend, got {self.backend_type}")
        self._allocate_state()
        probs = np.abs(self._state)**2
        outcome = np.random.choice(range(2**self.num_qubits), p=probs)
        return outcome, probs
