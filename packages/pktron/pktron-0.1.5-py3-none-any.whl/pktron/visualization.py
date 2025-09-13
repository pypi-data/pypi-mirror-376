
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from .backend import execute, StatevectorSimulator, StabilizerSimulator
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_histogram(circuit, shots=1024):
    backend = StabilizerSimulator() if circuit.backend_type == "stabilizer" else StatevectorSimulator()
    if circuit.num_qubits > 10:
        print("Warning: Large circuit, using low shots for plot.")
        shots = 100
    result = execute(circuit, backend, shots=shots)
    counts = result.get_counts()
    states = [f"|{i:0{circuit.num_qubits}b}⟩" for i in range(min(2**circuit.num_qubits, 1000))]
    probs = [counts.get(f"{i:0{circuit.num_qubits}b}", 0) / shots for i in range(min(2**circuit.num_qubits, 1000))]
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    x = range(len(states))
    y = [1] * len(states)
    z = [0] * len(states)
    dx = [0.4] * len(states)
    dy = [0.4] * len(states)
    dz = probs
    num_states = len(states)
    colors = cm.viridis(np.linspace(0, 1, num_states))
    ax.bar3d(x, y, z, dx, dy, dz, color=colors, alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(states, rotation=45, ha='right')
    ax.set_yticks([])
    ax.set_zlabel('Probability', fontsize=12)
    ax.set_title('PKTron Quantum Histogram', fontsize=14, color='darkblue')
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.show()
    return counts

def plot_histogram_interactive(circuit, shots=1024):
    backend = StabilizerSimulator() if circuit.backend_type == "stabilizer" else StatevectorSimulator()
    result = execute(circuit, backend, shots=shots)
    counts = result.get_counts()
    states = sorted(counts.keys())
    probs = [counts[state] / shots for state in states]
    fig = go.Figure(data=[go.Bar(x=states, y=probs, marker_color='blue')])
    fig.update_layout(title='PKTron Interactive Quantum Histogram', xaxis_title='State', yaxis_title='Probability')
    fig.show()
    return counts

def partial_trace(rho, keep):
    dims = int(np.sqrt(rho.shape[0]))
    n = int(np.log2(dims))
    dims_list = [2] * n
    rho = rho.reshape(dims_list + dims_list)
    trace_axes = [i for i in range(n) if i not in keep] + [i + n for i in range(n) if i not in keep]
    for ax in sorted(trace_axes, reverse=True):
        rho = np.trace(rho, axis1=ax, axis2=ax)
    return rho

def get_bloch_vector(rho):
    pauli_x = np.array([[0, 1], [1, 0]])
    pauli_y = np.array([[0, -1j], [1j, 0]])
    pauli_z = np.array([[1, 0], [0, -1]])
    x = np.real(np.trace(rho @ pauli_x))
    y = np.real(np.trace(rho @ pauli_y))
    z = np.real(np.trace(rho @ pauli_z))
    return x, y, z

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

def plot_bloch_interactive(circuit):
    if circuit.backend_type != "statevector":
        raise ValueError(f"Bloch requires statevector backend, got {circuit.backend_type}")
    psi = circuit.get_state()
    rho = np.outer(psi, psi.conj())
    n = circuit.num_qubits
    if n > 5:
        raise ValueError("Interactive multi-Bloch supports up to 5 qubits for performance.")
    cols = min(n, 3)
    rows = (n // cols) + (n % cols > 0)
    fig = make_subplots(rows=rows, cols=cols, specs=[[{'type': 'scene'} for _ in range(cols)] for _ in range(rows)],
                        subplot_titles=[f'Qubit {i}' for i in range(n)])
    for q in range(n):
        rho_q = partial_trace(rho, [q])
        x, y, z = get_bloch_vector(rho_q)
        row = (q // cols) + 1
        col = (q % cols) + 1
        # Sphere
        theta = np.linspace(0, np.pi, 30)
        phi = np.linspace(0, 2*np.pi, 30)
        theta, phi = np.meshgrid(theta, phi)
        xs = np.sin(theta) * np.cos(phi)
        ys = np.sin(theta) * np.sin(phi)
        zs = np.cos(theta)
        fig.add_trace(go.Surface(x=xs, y=ys, z=zs, opacity=0.2, colorscale='blues', showscale=False), row=row, col=col)
        # Vector
        fig.add_trace(go.Scatter3d(x=[0, x], y=[0, y], z=[0, z], mode='lines', line=dict(color='red', width=5)), row=row, col=col)
        fig.add_trace(go.Scatter3d(x=[x], y=[y], z=[z], mode='markers', marker=dict(size=5, color='red')), row=row, col=col)
        fig.update_layout(scene=dict(aspectmode='cube'))
    fig.update_layout(title='PKTron Interactive Bloch Spheres', height=300*rows, width=300*cols)
    fig.show()
