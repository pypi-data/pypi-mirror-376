# PKTron: Pakistan Tron Quantum Simulator

PKTron is a 100 Qubit quantum circuit simulator and Pakistan's 1st Quantum Simulator for 100 Qubits - Version 0.1.5 supporting statevector, stabilizer, and MPS backends. It provides tools for quantum circuit simulation, visualization (including interactive 3D Bloch spheres using Plotly), and quantum algorithms.

## Installation
```bash
pip install pktron
```

## Usage
### Basic Circuit
```python
from pktron import QuantumCircuit, execute, StatevectorSimulator
from pktron.gates import h, cnot

qc = QuantumCircuit(2, "statevector")
h(qc, 0)
cnot(qc, 0, 1)
qc.draw()  # Visualize the quantum circuit
plot_bloch_interactive(qc)  # Interactive 3D Bloch spheres for each qubit
result = execute(qc, StatevectorSimulator())
print(result.get_counts())
plot_histogram_interactive(qc)  # Interactive histogram
```

### BB84 Quantum Key Distribution
```python
from pktron.algorithms import bb84_qkd

result = bb84_qkd(num_qubits=8, eve_intercept_prob=0.5, seed=42)
print("Alice's key:", result["alice_key"])
print("Bob's key:", result["bob_key"])
print("Error rate:", result["error_rate"])
print("Eve detected:", result["eve_detected"])
result["circuit"].draw()  # Visualize the QKD circuit
```

## Features
- Quantum circuit simulation with multiple backends
- Visualization of quantum states (histogram, Bloch sphere for 1 qubit)
- Interactive 3D visualizations with Plotly for Bloch spheres (single or multi-qubit) and histograms, providing better interactivity than Qiskit's static plots
- Circuit visualization with `.draw()` method using Matplotlib and NetworkX
- Basic quantum algorithms (e.g., Quantum Treasure Hunt)
- BB84 Quantum Key Distribution with Eve's interception simulation
- Measurements handled via statevector backend with classical post-processing

## Notes
- The interactive visualizations require Plotly and are designed to be way better than Qiskit's by offering rotatable 3D views and subplots for multi-qubit states.
- For multi-qubit Bloch, reduced density matrices are computed for each qubit to display individual Bloch spheres.

## License
MIT License
