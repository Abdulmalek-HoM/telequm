import numpy as np
from IPython.core.display_functions import display
from qiskit import QuantumCircuit, transpile
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt

# Safe imports for simulation backends
try:
    from qiskit_aer import AerSimulator
    AER_AVAILABLE = True
except ImportError:
    AER_AVAILABLE = False

def c_amod15(a, power):
    """ Controlled multiplication by a^(2^power) mod 15. """
    if a not in [2, 7, 8, 11, 13]:
        raise ValueError("Base 'a' must be coprime to 15 (2, 7, 8, 11, or 13)")
        
    U = QuantumCircuit(4)        
    for _ in range(2**power):
        if a in [2, 13]:
            U.swap(0, 1); U.swap(1, 2); U.swap(2, 3)
            if a == 13:
                for q in range(4): U.x(q)
        elif a in [7, 8]:
            U.swap(2, 3); U.swap(1, 2); U.swap(0, 1)
            if a == 7:
                for q in range(4): U.x(q)
        elif a == 11:
            U.swap(0, 2); U.swap(1, 3)
            for q in range(4): U.x(q)
                
    U = U.to_gate()
    U.name = f"{a}^{2**power} mod 15"
    c_U = U.control()
    return c_U

def qft_inverse(n):
    """ Constructs a custom Inverse Quantum Fourier Transform (IQFT) circuit. """
    qc = QuantumCircuit(n)
    for qubit in range(n // 2):
        qc.swap(qubit, n - qubit - 1)
    for j in range(n):
        for m in range(j):
            qc.cp(-np.pi / float(2**(j - m)), m, j)
        qc.h(j)
    qc.name = "IQFT"
    return qc

def continued_fraction_convergents(val, max_denominator):
    convergents = []
    remain = val
    a = []
    for _ in range(20):
        floor_val = int(remain)
        a.append(floor_val)
        diff = remain - floor_val
        if diff < 1e-10: break
        remain = 1.0 / diff
    p_prev2, p_prev1 = 0, 1
    q_prev2, q_prev1 = 1, 0
    for coeff in a:
        p = coeff * p_prev1 + p_prev2
        q = coeff * q_prev1 + q_prev2
        if q > max_denominator: break
        convergents.append((p, q))
        p_prev2, p_prev1 = p_prev1, p
        q_prev2, q_prev1 = q_prev1, q
    return convergents

def classical_gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def run_shors_qiskit(a=7):
    N = 15
    print("=" * 60)
    print(f"SHOR'S ALGORITHM VIA QISKIT - FACTORING N = {N} (base a = {a})")
    print("=" * 60)
    
    t = 8  # Control qubits
    n = 4  # Target qubits
    
    # 1. Build circuit
    qc = QuantumCircuit(t + n, t)
    
    # Initialize control register into superposition
    for q in range(t):
        qc.h(q)
        
    # Initialize target register to auxiliary state |1>
    qc.x(t)
    
    # Apply Controlled Modular Exponentiation
    print("Adding controlled modular multiplication gates...")
    for q in range(t):
        qc.append(c_amod15(a, q), [q] + [i + t for i in range(n)])
        
    # Run the Inverse QFT to translate phase frequencies
    qc.append(qft_inverse(t), range(t))
    qc.measure(range(t), range(t))
    
    # --- VISUALIZATION: DISPLAY CIRCUIT ---
    print("\n--- High-Level Quantum Circuit Map ---")

    display(qc.draw(output='mpl'))
    # --------------------------------------
    
    if not AER_AVAILABLE:
        print("\n[WARNING] qiskit-aer is not installed. Execution aborted.")
        return
        
    print("\nRunning local simulation on AerSimulator...")
    simulator = AerSimulator()
    compiled_circuit = transpile(qc, simulator)
    job = simulator.run(compiled_circuit, shots=1024)
    counts = job.result().get_counts()
    
    # Plot and save measurement histogram in background
    fig_hist = plot_histogram(counts)
    fig_hist.savefig('measurement_histogram.png', bbox_inches='tight')
    plt.close(fig_hist)
    print("- Saved measurement histogram -> 'measurement_histogram.png'")
    
    print("\nTop measured states and phase extractions:")
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    
    success = False
    for binary_str, count in sorted_counts[:5]:
        C = int(binary_str, 2)
        phase = C / (2**t)
        print(f"  |{binary_str}> (counts: {count:4d}) -> C = {C:3d} -> Phase = {phase:.6f}")
        
        if phase == 0:
            continue
            
        convergents = continued_fraction_convergents(phase, N)
        for p, q in convergents:
            if q == 0: continue
            for factor in range(1, 5):
                r = q * factor
                if r >= N: continue
                if pow(a, r, N) == 1:
                    if r % 2 == 0:
                        half_power = pow(a, r // 2, N)
                        if half_power != N - 1:
                            factor1 = classical_gcd(half_power - 1, N)
                            factor2 = classical_gcd(half_power + 1, N)
                            if factor1 > 1 and factor1 < N:
                                print(f"\nSUCCESS! Found period r = {r}")
                                print(f"Factors of {N} are: {factor1} and {factor2}")
                                success = True
                                break
            if success: break
        if success: break
            
    if not success:
        print("\nCould not factor 15 using top measurements. Try running again.")

if __name__ == "__main__":
    run_shors_qiskit(a=7)