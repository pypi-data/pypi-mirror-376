
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import seaborn as sns
from qutip import Qobj, ket2dm, Bloch
import imageio
import os
from .backend import execute, StatevectorSimulator, StabilizerSimulator
from .quantum import QuantumCircuit
from .gates import h, x, cnot, ry, cz, swap
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

def plot_histogram_interactive(circuits, shots=1024, labels=None):
    backend = StatevectorSimulator()
    if not isinstance(circuits, list):
        circuits = [circuits]
    if labels is None:
        labels = [f"Circuit {i+1}" for i in range(len(circuits))]
    fig = go.Figure()
    for circuit, label in zip(circuits, labels):
        if circuit.num_qubits > 10:
            print(f"Warning: Large circuit for {label}, using low shots.")
            shots = 100
        result = execute(circuit, backend, shots=shots)
        counts = result.get_counts()
        states = sorted(counts.keys())
        probs = [counts[state] / shots for state in states]
        fig.add_trace(go.Bar(x=states, y=probs, name=label, marker_color=f'rgb({np.random.randint(0,255)},{np.random.randint(0,255)},{np.random.randint(0,255)})'))
    fig.update_layout(
        title='PKTron Interactive Quantum Histogram (Multiple Runs)',
        xaxis_title='State',
        yaxis_title='Probability',
        barmode='overlay',
        bargap=0.1,
        bargroupgap=0.05
    )
    return fig

def partial_trace(rho, keep):
    n = int(np.log2(rho.shape[0]))
    dims_list = [2] * n + [2] * n
    rho = rho.reshape(*dims_list)
    keep = set(keep)
    current_dims = list(dims_list)
    traced_axes = []
    
    for i in range(n):
        if i not in keep:
            # Find the current index of the row and column axes for qubit i
            row_axis = i - len([j for j in traced_axes if j < i])
            col_axis = (n + i) - len([j for j in traced_axes if j < n + i])
            if row_axis < len(current_dims) // 2 and col_axis < len(current_dims):
                rho = np.trace(rho, axis1=row_axis, axis2=col_axis)
                current_dims.pop(row_axis)
                current_dims.pop(col_axis - 1)  # Adjust for the removed row_axis
                traced_axes.append(i)
                traced_axes.append(n + i)
            else:
                raise ValueError(f"Axis out of bounds: row_axis={row_axis}, col_axis={col_axis}, current_dims={current_dims}")
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
    psi = circuit.get_state()
    rho = np.outer(psi, psi.conj())
    n = circuit.num_qubits
    cols = min(n, 3)
    rows = (n // cols) + (n % cols > 0)
    fig = plt.figure(figsize=(6 * cols, 6 * rows))
    for q in range(n):
        try:
            rho_q = partial_trace(rho, [q])
            x, y, z = get_bloch_vector(rho_q)
            ax = fig.add_subplot(rows, cols, q + 1, projection='3d')
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
            ax.set_title(f'Qubit {q}', fontsize=12)
        except Exception as e:
            print(f"Warning: Failed to plot Bloch sphere for qubit {q}: {e}")
    fig.suptitle('PKTron Bloch Spheres', fontsize=14, color='darkblue')
    plt.tight_layout()
    plt.show()
    return fig

def plot_bloch_interactive(circuit, animate=False):
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
    
    frames = []
    if animate:
        temp_circuit = QuantumCircuit(n, "statevector")
        states = [np.array(temp_circuit.get_state())]
        for gate in circuit.gate_history:
            gate_parts = gate.split()
            gate_name = gate_parts[0]
            if gate_name == 'H':
                temp_circuit.h(int(gate_parts[-1]))
            elif gate_name == 'X':
                temp_circuit.x(int(gate_parts[-1]))
            elif gate_name == 'CNOT':
                temp_circuit.cnot(int(gate_parts[2]), int(gate_parts[4]))
            elif gate_name == 'Ry':
                temp_circuit.ry(int(gate_parts[-1]), float(gate_parts[1].strip('()')))
            elif gate_name == 'CZ':
                temp_circuit.cz(int(gate_parts[2]), int(gate_parts[4]))
            elif gate_name == 'SWAP':
                temp_circuit.swap(int(gate_parts[2]), int(gate_parts[4]))
            states.append(np.array(temp_circuit.get_state()))
    
    for q in range(n):
        rho_q = partial_trace(rho, [q])
        x, y, z = get_bloch_vector(rho_q)
        row = (q // cols) + 1
        col = (q % cols) + 1
        theta = np.linspace(0, np.pi, 30)
        phi = np.linspace(0, 2*np.pi, 30)
        theta, phi = np.meshgrid(theta, phi)
        xs = np.sin(theta) * np.cos(phi)
        ys = np.sin(theta) * np.sin(phi)
        zs = np.cos(theta)
        fig.add_trace(go.Surface(x=xs, y=ys, z=zs, opacity=0.2, colorscale='blues', showscale=False), row=row, col=col)
        fig.add_trace(go.Scatter3d(x=[0, x], y=[0, y], z=[0, z], mode='lines', line=dict(color='red', width=5)), row=row, col=col)
        fig.add_trace(go.Scatter3d(x=[x], y=[y], z=[z], mode='markers', marker=dict(size=5, color='red')), row=row, col=col)
    
    if animate:
        for i, state in enumerate(states):
            frame_data = []
            rho = np.outer(state, state.conj())
            for q in range(n):
                rho_q = partial_trace(rho, [q])
                x, y, z = get_bloch_vector(rho_q)
                row = (q // cols) + 1
                col = (q % cols) + 1
                frame_data.extend([
                    go.Surface(x=xs, y=ys, z=zs, opacity=0.2, colorscale='blues', showscale=False),
                    go.Scatter3d(x=[0, x], y=[0, y], z=[0, z], mode='lines', line=dict(color='red', width=5)),
                    go.Scatter3d(x=[x], y=[y], z=[z], mode='markers', marker=dict(size=5, color='red'))
                ])
            frames.append(go.Frame(data=frame_data, name=f'frame{i}'))
        fig.frames = frames
        fig.update_layout(
            updatemenus=[{
                'buttons': [
                    {'args': [None, {'frame': {'duration': 500, 'redraw': True}, 'fromcurrent': True}],
                     'label': 'Play', 'method': 'animate'},
                    {'args': [[None], {'frame': {'duration': 0, 'redraw': True}, 'mode': 'immediate'}],
                     'label': 'Pause', 'method': 'animate'}
                ],
                'direction': 'left', 'pad': {'r': 10, 't': 87}, 'showactive': True,
                'type': 'buttons', 'x': 0.1, 'xanchor': 'right', 'y': 0, 'yanchor': 'top'
            }]
        )
    
    fig.update_layout(title='PKTron Interactive Bloch Spheres', height=300*rows, width=300*cols)
    for i in range(1, rows*cols + 1):
        fig.update_scenes(aspectmode='cube', xaxis_title='X', yaxis_title='Y', zaxis_title='Z', row=(i-1)//cols+1, col=(i-1)%cols+1)
    return fig

def plot_error_analysis(circuit, shots=1024, noise_prob=0.1):
    backend = StatevectorSimulator()
    counts_list = []
    for _ in range(10):
        noisy_counts = {}
        for _ in range(shots):
            temp_circuit = QuantumCircuit(circuit.num_qubits, "statevector")
            for gate in circuit.gate_history:
                gate_parts = gate.split()
                gate_name = gate_parts[0]
                if gate_name == 'H':
                    temp_circuit.h(int(gate_parts[-1]))
                elif gate_name == 'X':
                    temp_circuit.x(int(gate_parts[-1]))
                elif gate_name == 'CNOT':
                    temp_circuit.cnot(int(gate_parts[2]), int(gate_parts[4]))
                elif gate_name == 'Ry':
                    temp_circuit.ry(int(gate_parts[-1]), float(gate_parts[1].strip('()')))
                elif gate_name == 'CZ':
                    temp_circuit.cz(int(gate_parts[2]), int(gate_parts[4]))
                elif gate_name == 'SWAP':
                    temp_circuit.swap(int(gate_parts[2]), int(gate_parts[4]))
                if np.random.random() < noise_prob:
                    temp_circuit.x(np.random.randint(0, circuit.num_qubits))
            outcome, _ = temp_circuit.measure()
            state = f"{outcome:0{circuit.num_qubits}b}"
            noisy_counts[state] = noisy_counts.get(state, 0) + 1
        counts_list.append(noisy_counts)
    
    states = sorted(set().union(*[set(counts.keys()) for counts in counts_list]))
    data = [[counts.get(state, 0) / shots for counts in counts_list] for state in states]
    
    plt.figure(figsize=(10, 6))
    sns.violinplot(data=data, inner="box")
    plt.xticks(range(len(states)), states, rotation=45)
    plt.xlabel('Quantum States')
    plt.ylabel('Probability')
    plt.title('PKTron Error Analysis (Noisy Measurements)')
    plt.tight_layout()
    plt.show()
    return data

def plot_density_matrix(circuit, save_gif=False):
    if circuit.backend_type != "statevector":
        raise ValueError(f"Density matrix requires statevector backend, got {circuit.backend_type}")
    psi = circuit.get_state()
    rho = ket2dm(Qobj(psi, dims=[[2]*circuit.num_qubits, [1]*circuit.num_qubits]))
    fig, ax = plt.subplots(figsize=(8, 6))
    matrix = np.abs(rho.full())
    sns.heatmap(matrix, cmap='viridis', ax=ax)
    ax.set_title('PKTron Density Matrix Heatmap')
    plt.show()
    
    if save_gif:
        temp_circuit = QuantumCircuit(circuit.num_qubits, "statevector")
        images = []
        filename = "density_evolution.gif"
        for gate in circuit.gate_history:
            gate_parts = gate.split()
            gate_name = gate_parts[0]
            if gate_name == 'H':
                temp_circuit.h(int(gate_parts[-1]))
            elif gate_name == 'X':
                temp_circuit.x(int(gate_parts[-1]))
            elif gate_name == 'CNOT':
                temp_circuit.cnot(int(gate_parts[2]), int(gate_parts[4]))
            elif gate_name == 'Ry':
                temp_circuit.ry(int(gate_parts[-1]), float(gate_parts[1].strip('()')))
            elif gate_name == 'CZ':
                temp_circuit.cz(int(gate_parts[2]), int(gate_parts[4]))
            elif gate_name == 'SWAP':
                temp_circuit.swap(int(gate_parts[2]), int(gate_parts[4]))
            psi = temp_circuit.get_state()
            rho = ket2dm(Qobj(psi, dims=[[2]*circuit.num_qubits, [1]*circuit.num_qubits]))
            fig, ax = plt.subplots(figsize=(4, 3))
            sns.heatmap(np.abs(rho.full()), cmap='viridis', ax=ax)
            ax.set_title(f'Density Matrix (Gate: {" ".join(gate_parts[:2] if len(gate_parts) > 1 else gate_parts)})')
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            image = np.frombuffer(renderer.buffer_rgba(), dtype='uint8')
            image = image.reshape(fig.canvas.get_width_height()[::-1] + (4,))[:, :, :3]
            images.append(image)
            plt.close()
        imageio.mimsave(filename, images, fps=2)
        print(f"Density matrix evolution GIF saved as {filename}")
    return fig
