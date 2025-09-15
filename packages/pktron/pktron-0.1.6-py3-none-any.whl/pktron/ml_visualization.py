
import pennylane as qml
import numpy as np
import matplotlib.pyplot as plt

def variational_circuit(params, num_qubits):
    dev = qml.device('default.qubit', wires=num_qubits)
    @qml.qnode(dev)
    def circuit(params):
        for i in range(num_qubits):
            qml.RX(params[i], wires=i)
        if num_qubits > 1:
            qml.CNOT(wires=[0, 1])
        return qml.expval(qml.PauliZ(0))
    return circuit

def plot_loss_landscape(num_qubits=2, steps=20):
    params = np.linspace(-np.pi, np.pi, steps)
    X, Y = np.meshgrid(params, params)
    Z = np.zeros_like(X)
    circuit = variational_circuit([0, 0], num_qubits)
    for i in range(steps):
        for j in range(steps):
            Z[i, j] = circuit([X[i, j], Y[i, j]])
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(X, Y, Z, cmap='viridis')
    ax.set_xlabel('Param 1')
    ax.set_ylabel('Param 2')
    ax.set_zlabel('Expectation Value')
    ax.set_title('PKTron Loss Landscape')
    plt.show()
