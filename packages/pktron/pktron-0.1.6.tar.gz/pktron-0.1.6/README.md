
# PKTron: Pakistan Quantum Tron Simulator 

PKTron Pakistan's 1st Quantum Simulator with 100 Qubits Capability Version 0.1.6 it has a library for quantum computing simulations, offering quantum circuit construction, quantum algorithms, and advanced visualizations integrated with machine learning capabilities.

## Features
- Quantum circuit simulation with statevector, stabilizer, and MPS backends
- Implementation of quantum algorithms: QFT, Phase Estimation, Shor's, VQE, QAOA, HHL
- Visualization tools: Histograms, Bloch spheres, density matrices
- Machine learning integration with variational circuits and loss landscapes
- Support for noisy simulations and error analysis

## Installation
```bash
pip install pktron
```

## Usage
```python
from pktron import QuantumCircuit, plot_histogram, bb84_qkd

# Create a quantum circuit
qc = QuantumCircuit(2)
qc.h(0)
qc.cnot(0, 1)

# Visualize
plot_histogram(qc)

# Run BB84 QKD
result = bb84_qkd(4)
print(result['alice_key'], result['bob_key'])
```

## Requirements
- Python >= 3.7
- numpy>=1.21.0
- pennylane>=0.38.0
- matplotlib>=3.4.0
- quimb>=1.4.0
- networkx>=2.8.0
- plotly>=5.0.0
- seaborn>=0.11.0
- qutip>=4.6.0
- imageio>=2.9.0

## License
MIT License
