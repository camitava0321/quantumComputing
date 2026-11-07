# Qiskit Jupyter Notebooks — Getting Started Guide

> **Audience:** Quantum computing newcomers who want to run these notebooks locally using the `amc-qm` Python virtual environment.

---

## 1. Prerequisites

### Python virtual environment

All notebooks are configured to use the `amc-qm` venv located at:

```
H:\DevelopmentWorkspaces\python-envs\amc-qm\
```

Key packages already installed in that venv:

| Package | Version | Purpose |
|---|---|---|
| `qiskit` | 2.5.x | Core quantum computing framework |
| `qiskit-aer` | 0.17.x | High-performance local simulator |
| `qiskit-ibm-runtime` | 0.48.x | Run on real IBM Quantum hardware |
| `qiskit-algorithms` | 0.4.x | Grover, VQE, amplitude estimation, eigensolvers (former Aqua algorithms) |
| `qiskit-machine-learning` | 0.9.x | QNNs, VQC, QSVC / quantum kernels, `ad_hoc_data` (`4xx`, `7xx`) |
| `qiskit-optimization` | 0.7.x | `QuadraticProgram`, Grover / QAOA / ADMM optimizers (`3xx`, `5xx`) |
| `docplex`, `scikit-learn` | — | Model building (`5xx`) and classical datasets / SVMs (`4xx`, `7xx`) |
| `torch` (CPU) | 2.15.x | Discriminator and training loop of the quantum GANs (`421`–`425`) |
| `pandas` | 3.0.x | Reading the car-sale data (`423`) |
| `jupyter` / `notebook` | — | Interactive notebook environment |

### Register the kernel (one-time setup)

Open a terminal and run:

```powershell
# Activate the venv
H:\DevelopmentWorkspaces\python-envs\amc-qm\Scripts\activate.ps1

# Register it as a Jupyter kernel named "amc-qm"
python -m ipykernel install --user --name amc-qm --display-name "amc-qm (Python 3)"
```

---

## 2. Opening the Notebooks

```powershell
# Activate the venv
H:\DevelopmentWorkspaces\python-envs\amc-qm\Scripts\activate.ps1

# Launch Jupyter from the notebook directory
cd H:\DevelopmentWorkspaces\gitProjects\quantumcomputing-amc\qiskit-jupyter-notebooks_dev
jupyter notebook
```

In the Jupyter file browser, click any `.ipynb` file to open it.

> **Make sure the kernel shown in the top-right corner reads `amc-qm (Python 3)`.**
> If it shows something else, go to **Kernel → Change kernel → amc-qm (Python 3)**.

---

## 3. The Backend Setup Cell

Every notebook (except the pure linear-algebra ones in `001-QuantumQC-basic0-*`) starts with a **Backend Setup cell** that looks like this:

```python
# === BACKEND SETUP (qiskit_backend_config) ===
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath('__file__')))
from qiskit_backend_config import (get_backend, execute, Aer, BasicAer,
                                   IBMQ, least_busy, job_monitor, assemble, combine)

# ── Choose your backend here ──────────────────────────────────────────────
BACKEND_NAME = "qasm_simulator"   # <-- CHANGE THIS LINE to switch backend
IBM_QUANTUM_TOKEN = os.environ.get("IBM_QUANTUM_TOKEN", "")

backend = get_backend(BACKEND_NAME, token=_token_arg)
print(f'Backend ready: {backend}')
```

**Always run this cell first** (or use **Cell → Run All**). Everything else in the notebook depends on it.

---

## 4. Choosing Your Backend

### Option A — Local Simulator (default, no account needed)

Change `BACKEND_NAME` to one of these strings:

| Name | What it does |
|---|---|
| `"qasm_simulator"` | Shot-based measurements — counts how often each bitstring appears. Use this for most algorithms. |
| `"statevector_simulator"` | Keeps the full quantum state in memory. Best for learning and small circuits (≤ ~20 qubits). |
| `"unitary_simulator"` | Computes the full unitary matrix of the circuit. Useful for verifying gate sequences. |

Example:

```python
BACKEND_NAME = "statevector_simulator"
```

### Option B — Real IBM Quantum Hardware

#### Step 1 — Get an IBM Quantum account

Sign up (free) at [https://quantum.ibm.com](https://quantum.ibm.com) and copy your **API token** from your account profile.

#### Step 2 — Set your token

**Either** set it as an environment variable before launching Jupyter (recommended — keeps your token out of the notebook):

```powershell
$env:IBM_QUANTUM_TOKEN = "paste_your_token_here"
jupyter notebook
```

**Or** paste it directly into the setup cell (not recommended for shared machines):

```python
IBM_QUANTUM_TOKEN = "paste_your_token_here"
```

#### Step 3 — Pick a device

```python
BACKEND_NAME = "ibm_brisbane"   # a specific named device
# or
BACKEND_NAME = "least_busy"     # auto-pick the least-queued device that fits your circuit
```

> **Tip:** Real hardware jobs go into a queue and may take minutes or longer to complete, depending on demand. For learning and experimentation, always start with the simulator.

---

## 5. Running a Notebook

1. Open the notebook in Jupyter.
2. Confirm the kernel is `amc-qm (Python 3)` (top-right corner).
3. Click the first cell (the Backend Setup cell) and press **Shift+Enter** to run it. You should see:
   ```
   Backend ready: AerSimulator('aer_simulator')
   ```
4. Continue pressing **Shift+Enter** to run each cell in order, **or** use **Cell → Run All** to run everything at once.

---

## 6. Common Patterns You Will See

These patterns appear throughout the notebooks. They all work with the `amc-qm` venv as-is:

```python
# Building a circuit
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

# Running it (uses the backend variable set in the setup cell)
job    = execute(qc, backend, shots=1024)
result = job.result()
counts = result.get_counts()
print(counts)  # e.g. {'00': 512, '11': 512}

# Visualising results
from qiskit.visualization import plot_histogram
plot_histogram(counts)
```

### Getting a statevector

```python
sv_backend = get_backend("statevector_simulator")
job    = execute(qc, sv_backend)
result = job.result()
sv     = result.get_statevector()
print(sv)
```

### Getting a unitary matrix

```python
u_backend = get_backend("unitary_simulator")
job    = execute(qc, u_backend)
result = job.result()
U      = result.get_unitary()
print(U)
```

---

## 7. Notebook Organisation

| Prefix | Topic |
|---|---|
| `001-QuantumQC-basic0-*` | Linear algebra refresher (NumPy only, no qiskit runtime) |
| `001-QuantumQC-basic1/2/3-*` | Qubits, superposition, basic circuits |
| `001-QuantumQC-basics-*` | Circuit fundamentals, visualisation, backends |
| `002-QuantumCircuits-*` | Circuit construction and composition |
| `003-*` | Single-qubit gates, phase, state visualisation |
| `004-*` | Two-qubit gates |
| `005-*` | Diagonal and three-qubit gates |
| `006-*` | Non-unitary operations (measurement, reset) |
| `007-*` | Custom and constructed gates |
| `008-*` | Barriers and transpilers |
| `009-010` | Fun demos — quantum dice, emoticons |
| `011-015` | Density operators, encodings, MPS simulation, pulse |
| `021-*` | Teleportation, random number generation, 3-SAT |
| `022-*` | Core algorithms: Deutsch-Jozsa, Bernstein-Vazirani, Grover, QFT, QPE, Shor, Simon |
| `032-*` | Noise, error, superdense coding |
| `101-*` | Variational forms |
| `301-321-*` | AQUA algorithms (amplitude estimation, HHL, Grover optimisation) |
| `402-416-*` | Quantum ML — datasets, classifiers (QNN, VQC), quantum kernels (QSVM) |
| `420-425-*` | Quantum ML — quantum GANs (qGAN) |
| `501-505-*` | Combinatorial optimisation (QAOA, ADMM) |
| `701-703-*` | Quantum chemistry, variational linear solver |
| `A101-*` | Advanced AQUA (VQE, optimisation) |

### Quantum Machine Learning learning path

The QML notebooks are numbered in the order they should be read.  Each one starts with its
learning goals and prerequisites and ends with key takeaways, exercises and a pointer to the next
notebook.

**Stage 0 – building blocks** (from the general track)

| # | Notebook | Why |
|---|---|---|
| 1 | `008-03-Primitives-Estimator` | `EstimatorQNN` is built on the Estimator |
| 2 | `008-04-Primitives-Sampler` | `SamplerQNN`, `VQC` and the qGAN generator are built on the Sampler |
| 3 | `002-QuantumCircuits-006-SwapTest` | measuring state overlap – the idea behind quantum kernels |
| 4 | `013-EncodingStatevector` | loading classical data into amplitudes |
| 5 | `101-VariationalForms-TwoLocal` | parameterised circuits (ansätze) |

**Stage 1 – data and concepts**

| # | Notebook | Why |
|---|---|---|
| 6 | `402-QML-Datasets` | the datasets used throughout; why QML uses few features |
| 7 | `403-Variational-Classifier-From-Scratch` | a variational classifier built by hand: encoding, circuit, Hadamard-test gradients, training |

**Stage 2 – supervised QML with `qiskit-machine-learning`**

| # | Notebook | Why |
|---|---|---|
| 8 | `410-QNN-Classifier-EstimatorQNN` | QNN with an expectation-value output |
| 9 | `411-QNN-Classifier-SamplerQNN` | QNN with a measurement-probability output (same data as 410) |
| 10 | `412-QNN-Classifier-VQC` | the all-in-one `VQC` (same data as 410) |
| 11 | `413-VQC-AdHoc-Dataset` | VQC on the ad hoc dataset, with a train / test split |
| 12 | `415-QSVM-Binary` | quantum kernels vs a classical RBF kernel |
| 13 | `416-QSVM-Multiclass` | more than two classes |

**Stage 3 – generative QML (quantum GANs)**

| # | Notebook | Why |
|---|---|---|
| 14 | `303-Generate Random Variates` *(optional)* | sampling distributions with circuits |
| 15 | `420-QGAN-01-Generator-vs-Discriminator-Toy` | the two roles, with fixed circuits |
| 16 | `421-QGAN-02-LogNormal-1D` | a complete qGAN, every step written out |
| 17 | `422-QGAN-03-Correlated-2D` | 2-D data; why correlations need entanglement |
| 18 | `423-QGAN-04-Car-Sale-Data` | a real dataset |
| 19 | `302-Simple Amplitude Estimation` → `424-QGAN-05-Option-Pricing` | capstone: a trained generator as input to amplitude estimation |
| 20 | `425-QGAN-06-Experiments` | what makes qGAN training stable |

Run times on a laptop CPU: most notebooks take 1–2 minutes; `403` takes about 4, the qGAN
notebooks `421`–`423` 3–5, and `425` about 10.

### Challenge Tests (`challenge-tests/`)

| Subfolder | Topic |
|---|---|
| `challenge-tests/advocate test 20200715-1/` | Qiskit Advocate Test 2020 — Terra, Aer, Ignis, Aqua questions |
| `challenge-tests/iqc2021/` | IBM Quantum Challenge 2021 — Toffoli, Shor, QEC, Pulse, VQE |
| `challenge-tests/test2/` | Challenge 4 — 16×16 unitary decomposition |

Each subfolder has its own `README.md` with per-notebook notes.
The top-level [`challenge-tests/README.md`](challenge-tests/README.md) covers the common setup.

---

## 8. The Common Backend Helper (`qiskit_backend_config.py`)

The file [`qiskit_backend_config.py`](qiskit_backend_config.py) in this directory is the shared module that every notebook imports. You do **not** need to edit it to change backends — just change `BACKEND_NAME` in the notebook's setup cell.

If you want to understand or extend it:

```python
from qiskit_backend_config import get_backend, execute, Aer, BasicAer

# All equivalent ways to get a local simulator:
b = get_backend("qasm_simulator")
b = Aer.get_backend("qasm_simulator")      # old Aer API — still works
b = BasicAer.get_backend("qasm_simulator") # old BasicAer API — still works

# IBM hardware (needs token):
b = get_backend("ibm_brisbane", token="your_token")
b = get_backend("least_busy",   token="your_token", min_num_qubits=5)
```

Besides `get_backend`, `execute`, `Aer` and `BasicAer`, it provides drop-ins for other APIs removed in Qiskit 1.0/2.0 that the older notebooks still use:

| Name | Replaces |
|---|---|
| `IBMQ` (`load_account`, `get_provider`, `backends`, ...) | `qiskit.IBMQ`. Uses `QiskitRuntimeService` when a token is set; otherwise falls back to the local simulator with a warning. |
| `least_busy`, `job_monitor` | `qiskit.providers.ibmq.least_busy`, `qiskit.tools.monitor.job_monitor` |
| `assemble` | `qiskit.assemble` (backends now run circuits directly) |
| `combine(a, b)` | `a + b` / `a += b` on circuits (adds missing registers, then appends `b`) |

The simulators it returns (`LegacyAerSimulator`) also behave like the old Aer simulators: `.run()` transpiles when needed, and in `statevector_simulator` / `unitary_simulator` mode it saves the statevector / unitary so `result.get_statevector()` / `get_unitary()` work.

Run `python qiskit_backend_config.py` from the command line to run its self-test.

### `qml_qgan.py`

Qiskit Aqua's `QGAN` class no longer exists in any Qiskit package. The qGAN notebooks use the modern pattern instead: the generator is a `SamplerQNN` wrapped in a `TorchConnector`, and the discriminator and training loop are plain PyTorch. `421` writes every step out; [`qml_qgan.py`](qml_qgan.py) packages the same code (`discretize`, `generator_circuit`, `make_generator`, `Discriminator`, `train_qgan`, ...) for `422`–`425`.

### Notebooks with changed content

Most notebooks only had API calls updated. Where a library was removed with no successor, the notebook was rebuilt from basic parts or kept as reference text:

| Notebook | What changed |
|---|---|
| `015-001-Pulse` | Qiskit Pulse was removed in Qiskit 2.0. The pulse code is kept as markdown for reference (needs `qiskit<1.0`). |
| `022-Shor's Algorithm` | Shor is no longer part of Qiskit; it is built from its parts (modular multiplication + QPE) for N = 15. |
| `304-*` (HHL) | HHL is no longer part of Qiskit; it is built from QPE, controlled rotations and uncomputation. `-Copy1`: the efficient `TridiagonalToeplitz` circuit is not reproduced, so both depths match. |
| `032-Noise and Error` | Qiskit Ignis was removed; the measurement-calibration fitter / filter is written out in the notebook. |
| `503-MinEigenOptimizer` | Reduced from 32 to 16 variables: 2^32 amplitudes do not fit in memory. |
| `701-Quantum Chemistry-Basics` | `qiskit.chemistry` was removed and PySCF does not run on Windows; the LiH steps are kept as text and VQE runs on the H2 Hamiltonian. |
| `703-Variational Quantum Linear Solver` | Stray dataset cells pasted from `701-AQUA-ML` were removed (see `402`); explanations added. |
| `403`, `410`–`416`, `420`–`425` (QML) | Renumbered into reading order (formerly `A102`, `401`, `405`–`408`, `410`–`415`), narrated for students and moved to the non-deprecated circuit-library functions (`zz_feature_map`, `real_amplitudes`, `n_local`). `403`: state preparation fixed (angles were doubled), trains on the square loss as in the paper. `421`–`423`, `425`: rewritten with `SamplerQNN` + PyTorch. `425` replaces a unit-test harness with training experiments. |

---

## 9. Re-running the Patchers

Two patcher scripts are available:

### Root notebooks (`update_notebooks.py`)

Patches all `.ipynb` files **at the root level** of this directory:

```powershell
H:\DevelopmentWorkspaces\python-envs\amc-qm\Scripts\python.exe update_notebooks.py
```

### Challenge-tests subfolders (`patch_challenge_tests.py`)

Patches all `.ipynb` files **inside `challenge-tests/`** (all subfolders):

```powershell
H:\DevelopmentWorkspaces\python-envs\amc-qm\Scripts\python.exe patch_challenge_tests.py
```

Both scripts are idempotent — they replace the existing setup cell rather than inserting a duplicate.

---

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'qiskit'` | Wrong kernel selected. Switch to **amc-qm (Python 3)** via Kernel menu. |
| `ModuleNotFoundError: No module named 'qiskit_backend_config'` | Run the setup cell first, or check that `qiskit_backend_config.py` is in the same directory. |
| `NameError: name 'backend' is not defined` | The Backend Setup cell (cell 0) was not run. Run it before any other cell. |
| `ImportError: BasicAer` or `ImportError: Aer` | These are removed in Qiskit 2.x. The setup cell's shims handle this — make sure the setup cell ran. |
| `ImportError: execute` | Same as above — `execute` was removed from `qiskit` in v2. The shim in the setup cell provides it. |
| IBM 403 / account disabled error | Those are stale outputs from old runs. Ignore them — they live in old cells that load IBMQ, which is replaced. Just run the cells that use `backend` from the setup cell. |
| Queue very long on real hardware | Switch to `BACKEND_NAME = "least_busy"` or use the simulator while waiting. |
| `TranspileError` on a large circuit | Some older notebooks target removed or renamed gates. Try `optimization_level=0` in the execute call or use the simulator. |
| `UserWarning: No IBM Quantum token set; using the local simulator` | Expected without a token: `IBMQ` / `provider.get_backend(...)` cells fall back to the local simulator. Set `IBM_QUANTUM_TOKEN` to use real hardware. |
| `ModuleNotFoundError: No module named 'qml_qgan'` | Start Jupyter from this directory (the `422`–`425` qGAN notebooks import `qml_qgan.py` from here). |
| `ModuleNotFoundError: No module named 'torch'` | Install CPU PyTorch into the venv: `python -m pip install torch --index-url https://download.pytorch.org/whl/cpu` |

---

*Generated for `amc-qm` venv — Qiskit 2.5.x / qiskit-aer 0.17.x / qiskit-ibm-runtime 0.48.x / qiskit-algorithms 0.4.x / qiskit-machine-learning 0.9.x / qiskit-optimization 0.7.x*
