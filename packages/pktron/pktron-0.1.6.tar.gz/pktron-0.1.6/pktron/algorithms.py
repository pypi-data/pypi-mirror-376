
import numpy as np
from fractions import Fraction
from scipy.optimize import minimize
from .gates import h, rx, ry, rz, cnot, cz, s, toffoli, t, x, swap
from .quantum import QuantumCircuit
import pennylane as qml

def quantum_flip(circuit):
    circuit.h(0)
    if circuit.num_qubits > 1:
        circuit.cnot(0, 1)
    circuit.rx(0, np.pi/4)
    circuit.gate_history.append("Quantum Flip")

def super_quantum_dance(circuit):
    circuit.h(0)
    if circuit.num_qubits > 1:
        circuit.ry(1, np.pi/2)
        circuit.cnot(0, 1)
    if circuit.num_qubits > 2:
        circuit.toffoli(0, 1, 2)
    circuit.t(0)
    circuit.gate_history.append("Super Quantum Dance")

def quantum_treasure_hunt(circuit):
    target_state = 2**circuit.num_qubits - 1
    circuit.h(0)
    if circuit.num_qubits > 1:
        circuit.cnot(0, 1)
        circuit.ry(1, np.random.uniform(0, np.pi))
    circuit.rx(0, np.random.uniform(0, np.pi))
    outcome, probs = circuit.measure()
    score = probs[target_state] * 100
    circuit.gate_history.append(f"Quantum Treasure Hunt (Score: {score:.1f})")
    return score

def quantum_magic_spin(circuit):
    target_state = 0
    circuit.rx(0, np.random.uniform(0, 2*np.pi))
    if circuit.num_qubits > 1:
        circuit.ry(1, np.random.uniform(0, np.pi))
        circuit.cz(0, 1)
    circuit.s(0)
    outcome, probs = circuit.measure()
    score = probs[target_state] * 100
    circuit.gate_history.append(f"Quantum Magic Spin (Score: {score:.1f})")
    return score

def bb84_qkd(num_qubits, eve_intercept_prob=0.5, seed=None):
    if seed is not None:
        np.random.seed(seed)
    
    qc = QuantumCircuit(num_qubits, "statevector")
    
    alice_bits = np.random.randint(0, 2, num_qubits)
    alice_bases = np.random.randint(0, 2, num_qubits)
    
    eve_intercepts = np.random.choice([0, 1], size=num_qubits, p=[1-eve_intercept_prob, eve_intercept_prob])
    eve_bases = np.random.randint(0, 2, num_qubits)
    
    bob_bases = np.random.randint(0, 2, num_qubits)
    
    for i in range(num_qubits):
        if alice_bits[i] == 1:
            qc.x(i)
        if alice_bases[i] == 1:
            qc.h(i)
    
    for i in range(num_qubits):
        if eve_intercepts[i]:
            if eve_bases[i] == 1:
                qc.h(i)
            if np.random.randint(0, 2) == 1:
                qc.x(i)
            if eve_bases[i] == 1:
                qc.h(i)
    
    for i in range(num_qubits):
        if bob_bases[i] == 1:
            qc.h(i)
    
    outcome, probs = qc.measure()
    measured_bits = [int(b) for b in format(outcome, f'0{qc.num_qubits}b')]
    
    alice_key = []
    bob_key = []
    for i in range(num_qubits):
        if alice_bases[i] == bob_bases[i]:
            alice_key.append(alice_bits[i])
            bob_key.append(measured_bits[i])
    
    error_count = sum(a != b for a, b in zip(alice_key, bob_key))
    error_rate = error_count / len(alice_key) if alice_key else 0.0
    
    eve_detected = error_rate > 0.25
    
    qc.gate_history.append(f"BB84 QKD (Error rate: {error_rate:.2f}, Eve detected: {eve_detected})")
    
    return {
        "alice_key": alice_key,
        "bob_key": bob_key,
        "error_rate": error_rate,
        "eve_detected": eve_detected,
        "alice_bases": alice_bases.tolist(),
        "bob_bases": bob_bases.tolist(),
        "eve_intercepts": eve_intercepts.tolist(),
        "circuit": qc
    }

def grover_search(num_qubits, target=None, oracle_func=None, iterations=None, noise_prob=0.0):
    if num_qubits < 2:
        raise ValueError("Grover's search requires at least 2 qubits")
    if target is None and oracle_func is None:
        raise ValueError("Either target or oracle_func must be provided")
    qc = QuantumCircuit(num_qubits, "statevector")
    
    if iterations is None:
        iterations = int(np.pi / 4 * np.sqrt(2**num_qubits))
    
    def default_oracle():
        target_bin = format(target, f'0{num_qubits}b')
        for i, bit in enumerate(target_bin[::-1]):
            if bit == '0':
                qc.x(i)
        qc.h(num_qubits-1)
        if num_qubits > 2:
            qc.toffoli(0, 1, num_qubits-1)
            for i in range(2, num_qubits-1):
                qc.toffoli(i, num_qubits-2, num_qubits-1)
        else:
            qc.cnot(0, 1)
        qc.h(num_qubits-1)
        for i, bit in enumerate(target_bin[::-1]):
            if bit == '0':
                qc.x(i)
    
    def diffusion():
        for i in range(num_qubits):
            qc.h(i)
            qc.x(i)
        qc.h(num_qubits-1)
        if num_qubits > 2:
            qc.toffoli(0, 1, num_qubits-1)
            for i in range(2, num_qubits-1):
                qc.toffoli(i, num_qubits-2, num_qubits-1)
        else:
            qc.cnot(0, 1)
        qc.h(num_qubits-1)
        for i in range(num_qubits):
            qc.x(i)
            qc.h(i)
    
    for i in range(num_qubits):
        qc.h(i)
    
    for _ in range(iterations):
        if oracle_func is not None:
            oracle_func(qc)
        else:
            default_oracle()
        if np.random.random() < noise_prob:
            qc.x(np.random.randint(0, num_qubits))
        diffusion()
        if np.random.random() < noise_prob:
            qc.x(np.random.randint(0, num_qubits))
    
    outcome, probs = qc.measure()
    qc.gate_history.append(f"Grover Search (Target: {target if target is not None else 'Custom Oracle'})")
    return {"circuit": qc, "outcome": outcome, "probs": probs}

def qft(circuit, start=0, end=None):
    if end is None:
        end = circuit.num_qubits
    if end > circuit.num_qubits or start < 0:
        raise ValueError("Invalid qubit range for QFT")
    
    for i in range(start, end):
        for j in range(i + 1, end):
            lambda_ = np.pi / (2 ** (j - i))
            circuit.rz(i, lambda_ / 2)
            circuit.cnot(i, j)
            circuit.rz(j, -lambda_ / 2)
            circuit.cnot(i, j)
            circuit.rz(j, lambda_ / 2)
        circuit.h(i)
    
    for i in range(start, (start + end) // 2):
        circuit.swap(i, end - 1 - (i - start))
    
    circuit.gate_history.append("Quantum Fourier Transform")

def phase_estimation(circuit, unitary, estimation_qubits, target_qubits):
    n_est = len(estimation_qubits)
    n_target = len(target_qubits)
    
    for q in estimation_qubits:
        circuit.h(q)
    
    for i, eq in enumerate(estimation_qubits):
        for _ in range(2**i):
            unitary(circuit, control=eq, targets=target_qubits)
    
    for i in range(n_est - 1, -1, -1):
        for j in range(i):
            lambda_ = -np.pi / (2 ** (i - j))
            circuit.rz(estimation_qubits[i], lambda_ / 2)
            circuit.cnot(estimation_qubits[i], estimation_qubits[j])
            circuit.rz(estimation_qubits[j], -lambda_ / 2)
            circuit.cnot(estimation_qubits[i], estimation_qubits[j])
            circuit.rz(estimation_qubits[j], lambda_ / 2)
        circuit.h(estimation_qubits[i])
    
    circuit.gate_history.append("Phase Estimation")
    outcome, probs = circuit.measure()
    measured_phase = outcome / (2**n_est)
    return {"circuit": circuit, "phase": measured_phase, "probs": probs}

def shor_period_finding(N, a, num_qubits=None):
    if num_qubits is None:
        num_qubits = 2 * int(np.ceil(np.log2(N))) + 1
    
    if num_qubits % 2 != 0:
        num_qubits += 1
    
    qc = QuantumCircuit(num_qubits, "statevector")
    
    counting_qubits = num_qubits // 2
    register_qubits = num_qubits - counting_qubits
    
    # Initialize counting qubits in superposition
    for i in range(counting_qubits):
        qc.h(i)
    
    # Initialize first register qubit to |1>
    qc.x(counting_qubits)
    
    # Apply controlled modular multiplication gates
    for i in range(counting_qubits):
        power = 2**(counting_qubits - 1 - i)
        v = pow(a, power, N)
        dim = 2 ** register_qubits
        gate = np.eye(dim, dtype=complex)
        for y in range(N):  # Only map valid states < N
            out_y = (v * y) % N
            if out_y < dim and y < dim:  # Ensure indices are within bounds
                gate[out_y, y] = 1
        # Extend gate to include control qubit
        full_gate = np.eye(2**(register_qubits + 1), dtype=complex)
        full_gate[dim:2*dim, dim:2*dim] = gate
        control = i
        targets = list(range(counting_qubits, num_qubits))
        qubits_for_gate = [control] + targets
        qc._apply_gate(full_gate, qubits_for_gate)
        qc.gate_history.append(f"Controlled-Mult {v} mod {N} control {control} targets {targets}")
    
    # Apply inverse QFT to counting qubits
    for i in range(counting_qubits // 2):
        qc.swap(i, counting_qubits - 1 - i)
    for i in range(counting_qubits - 1, -1, -1):
        qc.h(i)
        for j in range(i - 1, -1, -1):
            lambda_ = -np.pi / (2 ** (i - j))
            qc.rz(j, lambda_ / 2)
            qc.cnot(j, i)
            qc.rz(i, -lambda_ / 2)
            qc.cnot(j, i)
            qc.rz(i, lambda_ / 2)
    
    period = None
    factors = []
    for _ in range(1000):  # Increased trials for robustness
        outcome, probs = qc.measure()
        measured = outcome >> register_qubits
        try:
            phase = measured / (2**counting_qubits)
            frac = Fraction(phase).limit_denominator(N)
            r = frac.denominator
            if r != 0 and r < N and pow(a, r, N) == 1:
                cand1 = np.gcd(pow(a, r//2, N) - 1, N)
                cand2 = np.gcd(pow(a, r//2, N) + 1, N)
                new_factors = [f for f in [cand1, cand2] if 1 < f < N]
                if new_factors:
                    period = r
                    factors = sorted(new_factors)
                    break
        except:
            pass
    
    if period is not None:
        qc.gate_history.append(f"Shor Period Finding (N={N}, a={a}, period={period})")
    else:
        qc.gate_history.append(f"Shor Period Finding (N={N}, a={a}, failed)")
    
    return {"circuit": qc, "period": period, "factors": factors}

def vqe(num_qubits, hamiltonian=None, ansatz_depth=3, noise_prob=0.0, max_iter=300):
    if hamiltonian is None:
        hamiltonian = np.diag([1.0 if i == 0 else -1.0 for i in range(2**num_qubits)])
    
    def ansatz(params, circuit):
        param_idx = 0
        for d in range(ansatz_depth):
            for i in range(num_qubits):
                circuit.ry(i, params[param_idx])
                circuit.rz(i, params[param_idx + num_qubits])
                param_idx += 1
            if num_qubits > 1:
                for i in range(num_qubits-1):
                    circuit.cnot(i, i+1)
            if np.random.random() < noise_prob:
                circuit.x(np.random.randint(0, num_qubits))
    
    def objective_function(params):
        qc = QuantumCircuit(num_qubits, "statevector")
        ansatz(params, qc)
        state = qc.get_state()
        energy = np.real(np.dot(state.conj(), np.dot(hamiltonian, state)))
        return energy
    
    initial_params = np.random.uniform(0, np.pi, 2 * num_qubits * ansatz_depth)
    
    result = minimize(objective_function, initial_params, method='Powell', options={'maxiter': max_iter})
    
    qc = QuantumCircuit(num_qubits, "statevector")
    ansatz(result.x, qc)
    energy = np.real(np.dot(qc.get_state().conj(), np.dot(hamiltonian, qc.get_state())))
    
    qc.gate_history.append(f"VQE (Energy: {energy:.4f}, Iterations: {result.nfev})")
    return {"circuit": qc, "energy": energy, "params": result.x}

def qaoa(num_qubits, graph=None, p=1, noise_prob=0.0, max_iter=100):
    if graph is None:
        graph = [(0, 1), (1, 2)] if num_qubits >= 3 else [(0, 1)]
    
    def cost_hamiltonian(circuit, gamma):
        for edge in graph:
            circuit.cz(edge[0], edge[1])
            if np.random.random() < noise_prob:
                circuit.x(np.random.randint(0, num_qubits))
    
    def mixer_hamiltonian(circuit, beta):
        for i in range(num_qubits):
            circuit.rx(i, 2 * beta)
    
    def objective_function(params):
        qc = QuantumCircuit(num_qubits, "statevector")
        for i in range(num_qubits):
            qc.h(i)
        for layer in range(p):
            gamma = params[2*layer]
            beta = params[2*layer + 1]
            cost_hamiltonian(qc, gamma)
            mixer_hamiltonian(qc, beta)
        outcome, probs = qc.measure()
        cut_value = sum(probs[i] * sum(1 for u, v in graph if (i >> u) & 1 != (i >> v) & 1) for i in range(2**num_qubits))
        return -cut_value
    
    initial_params = np.random.uniform(0, np.pi, 2*p)
    
    result = minimize(objective_function, initial_params, method='COBYLA', options={'maxiter': max_iter})
    
    qc = QuantumCircuit(num_qubits, "statevector")
    for i in range(num_qubits):
        qc.h(i)
    for layer in range(p):
        cost_hamiltonian(qc, result.x[2*layer])
        mixer_hamiltonian(qc, result.x[2*layer + 1])
    
    outcome, probs = qc.measure()
    cut_value = sum(probs[i] * sum(1 for u, v in graph if (i >> u) & 1 != (i >> v) & 1) for i in range(2**num_qubits))
    
    qc.gate_history.append(f"QAOA (Cut Value: {cut_value:.2f}, Iterations: {result.nfev})")
    return {"circuit": qc, "cut_value": cut_value, "params": result.x}

def hhl(num_qubits, matrix=None, vector=None):
    if matrix is None:
        matrix = np.array([[1, -1/2], [-1/2, 1]])
    if vector is None:
        vector = np.array([1, 0])
    
    if num_qubits < 3:
        raise ValueError("HHL requires at least 3 qubits (1 ancilla, 1 eigenvalue, 1 state)")
    
    if not np.allclose(matrix, matrix.conj().T):
        raise ValueError("Matrix must be Hermitian")
    
    n_state = int(np.log2(len(vector)))
    n_eigen = num_qubits - n_state - 1
    if 2**n_state != len(vector) or len(matrix) != len(vector):
        raise ValueError("Matrix and vector dimensions must match 2^n_state")
    
    qc = QuantumCircuit(num_qubits, "statevector")
    ancilla = 0
    eigen_qubits = list(range(1, n_eigen + 1))
    state_qubits = list(range(n_eigen + 1, num_qubits))
    
    # Initialize state qubits according to the input vector
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise ValueError("Input vector cannot be zero")
    vector = vector / norm  # Normalize input vector
    for i in range(n_state):
        if abs(vector[i]) > 1e-10:  # Avoid applying gates for near-zero amplitudes
            # Approximate the state preparation using rotations
            theta = 2 * np.arccos(vector[i]) if abs(vector[i]) <= 1 else np.pi
            qc.ry(state_qubits[i], theta)
    
    def unitary(circuit, control, targets):
        # Controlled rotation based on matrix norm
        theta = np.arccos(matrix[0, 0] / np.linalg.norm(matrix))
        for t in targets:
            # Construct controlled-RY gate matrix
            cos = np.cos(theta / 2)
            sin = np.sin(theta / 2)
            ry_gate = np.array([[cos, -sin], [sin, cos]])
            dim = 2**(len(targets) + 1)
            full_gate = np.eye(dim, dtype=complex)
            gate_slice = slice(2**len(targets), 2**(len(targets) + 1))
            full_gate[gate_slice, gate_slice] = ry_gate
            qubits_for_gate = [control] + [t]
            circuit._apply_gate(full_gate, qubits_for_gate)
            circuit.gate_history.append(f"Controlled-RY control {control} target {t}")
    
    # Apply phase estimation with controlled unitaries
    for i, eq in enumerate(eigen_qubits):
        for _ in range(2**i):
            unitary(qc, control=eq, targets=state_qubits)
    
    # Controlled rotations for eigenvalue inversion
    for i, q in enumerate(eigen_qubits):
        angle = np.pi / (2**(i+1))
        qc.cnot(q, ancilla)
        qc.ry(ancilla, angle)
        qc.cnot(q, ancilla)
    
    # Inverse QFT
    for i in range(n_eigen - 1, -1, -1):
        for j in range(i):
            angle = -np.pi / (2**(i-j))
            qc.rz(eigen_qubits[i], angle / 2)
            qc.cnot(eigen_qubits[i], eigen_qubits[j])
            qc.rz(eigen_qubits[j], -angle / 2)
            qc.cnot(eigen_qubits[i], eigen_qubits[j])
            qc.rz(eigen_qubits[j], angle / 2)
        qc.h(eigen_qubits[i])
    
    # Explicitly normalize the state before measurement
    qc.normalize()
    
    outcome, probs = qc.measure()
    # Normalize probabilities to ensure they sum to 1
    prob_sum = sum(probs)
    if abs(prob_sum) > 1e-10:  # Avoid division by zero
        probs = probs / prob_sum
    
    solution = np.zeros(2**n_state)
    for i in range(2**n_state):
        state = format(i, f'0{n_state}b')
        full_state = '1' + '0' * n_eigen + state  # Ancilla must be 1
        idx = int(full_state, 2)
        solution[i] = probs[idx] if idx < len(probs) else 0
    
    # Normalize the solution vector
    solution_norm = np.linalg.norm(solution)
    if solution_norm > 1e-10:
        solution = solution / solution_norm
    
    qc.gate_history.append(f"HHL (Solution norm: {np.linalg.norm(solution):.4f})")
    return {"circuit": qc, "solution": solution, "probs": probs}
