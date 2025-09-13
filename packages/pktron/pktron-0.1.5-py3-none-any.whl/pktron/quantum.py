
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

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

    def draw(self):
        """Draw the quantum circuit using Matplotlib and NetworkX."""
        fig, ax = plt.subplots(figsize=(max(10, len(self.gate_history) * 2), self.num_qubits * 0.5 + 2))
        ax.set_xlim(-0.5, len(self.gate_history) + 1.5)
        ax.set_ylim(-0.5, self.num_qubits - 0.5)
        ax.set_axis_off()

        # Draw qubit wires
        for q in range(self.num_qubits):
            ax.plot([0, len(self.gate_history) + 1], [q, q], 'k-', linewidth=1)
            ax.text(-0.2, q, f'q{q}', fontsize=12, ha='right', va='center')

        # Draw gates
        for layer, gate in enumerate(self.gate_history):
            parts = gate.split()
            gate_name = parts[0]
            if gate_name == 'H' or gate_name == 'X' or gate_name == 'Y' or gate_name == 'Z' or gate_name == 'S' or gate_name == 'S†' or gate_name == 'T' or gate_name == 'T†':
                qubit = int(parts[-1])
                ax.add_patch(plt.Rectangle((layer + 0.2, qubit - 0.2), 0.6, 0.4, facecolor='lightblue', edgecolor='black'))
                ax.text(layer + 0.5, qubit, gate_name, fontsize=8, ha='center', va='center')
            elif 'Rx' in gate_name or 'Ry' in gate_name or 'Rz' in gate_name:
                qubit = int(parts[-1])
                ax.add_patch(plt.Rectangle((layer + 0.2, qubit - 0.2), 0.6, 0.4, facecolor='lightgreen', edgecolor='black'))
                ax.text(layer + 0.5, qubit, gate_name[:2], fontsize=8, ha='center', va='center')
            elif gate_name == 'CNOT':
                control = int(parts[2])
                target = int(parts[4])
                ax.plot([layer + 0.5, layer + 0.5], [control, target], 'k-', linewidth=1)
                ax.add_patch(plt.Circle((layer + 0.5, control), 0.1, facecolor='black'))
                ax.add_patch(plt.Circle((layer + 0.5, target), 0.2, facecolor='white', edgecolor='black'))
                ax.text(layer + 0.5, target, 'X', fontsize=10, ha='center', va='center')
            elif gate_name in ['CZ', 'CY']:
                control = int(parts[2])
                target = int(parts[4])
                ax.plot([layer + 0.5, layer + 0.5], [control, target], 'k-', linewidth=1)
                ax.add_patch(plt.Circle((layer + 0.5, control), 0.1, facecolor='black'))
                ax.add_patch(plt.Circle((layer + 0.5, target), 0.1, facecolor='black'))
                ax.text(layer + 0.5, (control + target) / 2, gate_name, fontsize=8, ha='center', va='center')
            elif gate_name == 'SWAP':
                q1 = int(parts[2])
                q2 = int(parts[4])
                ax.plot([layer + 0.5, layer + 0.5], [q1, q2], 'k-', linewidth=1)
                ax.text(layer + 0.5, q1, '×', fontsize=12, ha='center', va='center')
                ax.text(layer + 0.5, q2, '×', fontsize=12, ha='center', va='center')
            elif gate_name == 'Toffoli':
                c1 = int(parts[2])
                c2 = int(parts[4])
                t = int(parts[6])
                qubits = sorted([c1, c2, t])
                ax.plot([layer + 0.5, layer + 0.5], [qubits[0], qubits[2]], 'k-', linewidth=1)
                ax.add_patch(plt.Circle((layer + 0.5, c1), 0.1, facecolor='black'))
                ax.add_patch(plt.Circle((layer + 0.5, c2), 0.1, facecolor='black'))
                ax.add_patch(plt.Circle((layer + 0.5, t), 0.2, facecolor='white', edgecolor='black'))
                ax.text(layer + 0.5, t, 'X', fontsize=10, ha='center', va='center')
            elif 'Quantum' in gate_name or 'Super' in gate_name or 'BB84' in gate_name:
                # Composite gates - draw a box spanning all qubits
                ax.add_patch(plt.Rectangle((layer + 0.1, -0.1), 0.8, self.num_qubits + 0.2, facecolor='yellow', edgecolor='black', alpha=0.7))
                ax.text(layer + 0.5, self.num_qubits / 2, gate_name, fontsize=10, ha='center', va='center', rotation=0)

        ax.set_title('PKTron Quantum Circuit Diagram', fontsize=14, color='darkblue', pad=20)
        plt.tight_layout()
        plt.show()
