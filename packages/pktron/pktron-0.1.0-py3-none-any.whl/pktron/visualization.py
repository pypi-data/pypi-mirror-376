
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def plot_histogram(circuit, shots=1024):
    if circuit.backend_type != "statevector":
        raise ValueError(f"Plot requires statevector backend, got {circuit.backend_type}")
    if circuit.num_qubits > 10:
        print("Warning: Large circuit, using low shots for plot.")
        shots = 100
    counts = {}
    for _ in range(shots):
        outcome, _ = circuit.measure()
        state = f"{outcome:0{circuit.num_qubits}b}"
        counts[state] = counts.get(state, 0) + 1
    states = [f"|{i:0{circuit.num_qubits}b}⟩" for i in range(2**circuit.num_qubits)]
    probs = [counts.get(f"{i:0{circuit.num_qubits}b}", 0) / shots for i in range(2**circuit.num_qubits)]
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    x = range(len(states))
    y = [1] * len(states)
    z = [0] * len(states)
    dx = [0.4] * len(states)
    dy = [0.4] * len(states)
    dz = probs
    colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99'][:len(states)]
    ax.bar3d(x, y, z, dx, dy, dz, color=colors, alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(states, rotation=45, ha='right')
    ax.set_yticks([])
    ax.set_zlabel('Probability', fontsize=12)
    ax.set_title('PKTron Quantum Histogram', fontsize=14, color='darkblue')
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.show()
    return counts

def plot_bloch(circuit):
    if circuit.backend_type != "statevector":
        raise ValueError(f"Bloch requires statevector backend, got {circuit.backend_type}")
    if circuit.num_qubits != 1:
        raise ValueError("Bloch sphere is only for 1 qubit!")
    psi = circuit.get_state()
    x = 2 * np.real(psi[0] * np.conj(psi[1]))
    y = 2 * np.imag(psi[0] * np.conj(psi[1]))
    z = np.abs(psi[0])**2 - np.abs(psi[1])**2
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection='3d')
    u = np.linspace(0, 2 * np.pi, 20)
    v = np.linspace(0, np.pi, 20)
    x_sphere = np.outer(np.cos(u), np.sin(v))
    y_sphere = np.outer(np.sin(u), np.sin(v))
    z_sphere = np.outer(np.ones(np.size(u)), np.cos(v))
    ax.plot_surface(x_sphere, y_sphere, z_sphere, color='b', alpha=0.1)
    ax.scatter([x], [y], [z], color='red', s=100)
    ax.plot([0, x], [0, y], [0, z], color='red', linewidth=2)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('PKTron Bloch Sphere', fontsize=14, color='darkblue')
    plt.show()
