# PKTron: Pakistan Tron Quantum Simulator

PKTron is a 100 Qubit quantum circuit simulator and Pakistan's 1st Quantum Simulator for 100 Qubits - Version 0.1.1 supporting statevector, stabilizer, and MPS backends. It provides tools for quantum circuit simulation, visualization, and quantum algorithms.

## Installation
```bash
pip install pktron
```

## Usage
```python
from pktron import QuantumCircuit, execute, StatevectorSimulator
from pktron.gates import h, cnot

qc = QuantumCircuit(2, "statevector")
h(qc, 0)
cnot(qc, 0, 1)
result = execute(qc, StatevectorSimulator())
print(result.get_counts())
```

## Features
- Quantum circuit simulation with multiple backends
- Visualization of quantum states (histogram, Bloch sphere)
- Basic quantum algorithms (e.g., Quantum Treasure Hunt)

## License
MIT License
