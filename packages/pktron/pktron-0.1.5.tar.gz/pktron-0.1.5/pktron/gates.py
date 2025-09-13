
import numpy as np

def h(circuit, qubit):
    H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
    circuit._apply_single_qubit_gate(H, qubit)
    circuit.gate_history.append(f"H on qubit {qubit}")

def x(circuit, qubit):
    X = np.array([[0, 1], [1, 0])
    circuit._apply_single_qubit_gate(X, qubit)
    circuit.gate_history.append(f"X on qubit {qubit}")

def y(circuit, qubit):
    Y = np.array([[0, -1j], [1j, 0]])
    circuit._apply_single_qubit_gate(Y, qubit)
    circuit.gate_history.append(f"Y on qubit {qubit}")

def z(circuit, qubit):
    Z = np.array([[1, 0], [0, -1]])
    circuit._apply_single_qubit_gate(Z, qubit)
    circuit.gate_history.append(f"Z on qubit {qubit}")

def s(circuit, qubit):
    S = np.array([[1, 0], [0, 1j]])
    circuit._apply_single_qubit_gate(S, qubit)
    circuit.gate_history.append(f"S on qubit {qubit}")

def sdg(circuit, qubit):
    Sdg = np.array([[1, 0], [0, -1j]])
    circuit._apply_single_qubit_gate(Sdg, qubit)
    circuit.gate_history.append(f"S† on qubit {qubit}")

def t(circuit, qubit):
    T = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]])
    circuit._apply_single_qubit_gate(T, qubit)
    circuit.gate_history.append(f"T on qubit {qubit}")

def tdg(circuit, qubit):
    Tdg = np.array([[1, 0], [0, np.exp(-1j * np.pi / 4)]])
    circuit._apply_single_qubit_gate(Tdg, qubit)
    circuit.gate_history.append(f"T† on qubit {qubit}")

def rx(circuit, qubit, theta):
    cos = np.cos(theta / 2)
    sin = np.sin(theta / 2)
    RX = np.array([[cos, -1j * sin], [-1j * sin, cos]])
    circuit._apply_single_qubit_gate(RX, qubit)
    circuit.gate_history.append(f"Rx({theta:.2f}) on qubit {qubit}")

def ry(circuit, qubit, theta):
    cos = np.cos(theta / 2)
    sin = np.sin(theta / 2)
    RY = np.array([[cos, -sin], [sin, cos]])
    circuit._apply_single_qubit_gate(RY, qubit)
    circuit.gate_history.append(f"Ry({theta:.2f}) on qubit {qubit}")

def rz(circuit, qubit, theta):
    RZ = np.array([[np.exp(-1j * theta / 2), 0], [0, np.exp(1j * theta / 2)]])
    circuit._apply_single_qubit_gate(RZ, qubit)
    circuit.gate_history.append(f"Rz({theta:.2f}) on qubit {qubit}")

def cnot(circuit, control, target):
    gate = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])
    circuit._apply_two_qubit_gate(gate, control, target)
    circuit.gate_history.append(f"CNOT control {control} target {target}")

def cz(circuit, control, target):
    gate = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]])
    circuit._apply_two_qubit_gate(gate, control, target)
    circuit.gate_history.append(f"CZ control {control} target {target}")

def cy(circuit, control, target):
    gate = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, -1j], [0, 0, 1j, 0]])
    circuit._apply_two_qubit_gate(gate, control, target)
    circuit.gate_history.append(f"CY control {control} target {target}")

def swap(circuit, qubit1, qubit2):
    gate = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
    circuit._apply_two_qubit_gate(gate, qubit1, qubit2)
    circuit.gate_history.append(f"SWAP qubits {qubit1} and {qubit2}")

def toffoli(circuit, control1, control2, target):
    if circuit.num_qubits < 3:
        raise ValueError("Toffoli needs 3 qubits")
    gate = np.eye(8, dtype=complex)
    gate[6, 6] = 0
    gate[6, 7] = 1
    gate[7, 6] = 1
    gate[7, 7] = 0
    circuit._apply_three_qubit_gate(gate, control1, control2, target)
    circuit.gate_history.append(f"Toffoli control {control1},{control2} target {target}")
