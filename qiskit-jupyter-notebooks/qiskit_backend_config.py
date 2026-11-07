"""
qiskit_backend_config.py
========================
Common backend-selection helper for all Qiskit notebooks in this repo.
Targets the venv at H:\\DevelopmentWorkspaces\\python-envs\\amc-qm
  - qiskit          2.5.x
  - qiskit-aer      0.17.x  (AerSimulator)
  - qiskit-ibm-runtime 0.48.x  (replaces deprecated qiskit-ibmq-provider)

Usage
-----
At the TOP of each notebook, import or %run this module:

    %run qiskit_backend_config.py          # relative path when notebook is in the same dir
    # or
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath('__file__')))
    from qiskit_backend_config import get_backend, execute, Aer, BasicAer

Then use the helpers exactly as you used to use the old Qiskit API:

    backend = get_backend('qasm_simulator')          # -> AerSimulator (QASM mode)
    backend = get_backend('statevector_simulator')   # -> AerSimulator (SV mode)
    backend = get_backend('unitary_simulator')       # -> AerSimulator (unitary mode)
    backend = get_backend('aer_simulator')           # -> AerSimulator (auto)

    # To run on real IBM hardware (requires IBM Quantum account & API token):
    #   Set env var  IBM_QUANTUM_TOKEN=<your_token>  or pass token= explicitly.
    backend = get_backend('ibm_brisbane')            # -> IBMBackend via QiskitRuntimeService

    job    = execute(circuit, backend, shots=1024)   # drop-in for old qiskit.execute()
    result = job.result()
    counts = result.get_counts()

Backward-compatible shims
--------------------------
    Aer.get_backend(name)       # returns AerSimulator
    BasicAer.get_backend(name)  # returns AerSimulator (BasicAer is gone in Qiskit 2.x)
    IBMQ.load_account() / IBMQ.get_provider().get_backend(name)
                                # QiskitRuntimeService with a token, else the local simulator
    least_busy(backends), job_monitor(job), assemble(circuits)
    get_runtime_service(...)    # QiskitRuntimeService(...); retired / no-account -> fake backends
    combine(qc1, qc2)           # replaces the removed  qc1 + qc2  /  qc1 += qc2
"""

from __future__ import annotations

import os
import warnings
from typing import Any

# ── Qiskit 2.x core ───────────────────────────────────────────────────────────
from qiskit import transpile
from qiskit.providers import Backend

# Qiskit 2.5 lists a non-existent name ("draw") in qiskit.visualization.__all__,
# which makes ``from qiskit.visualization import *`` fail.  Drop missing names.
import qiskit.visualization as _qvis
_qvis.__all__ = [n for n in getattr(_qvis, "__all__", []) if hasattr(_qvis, n)]

# ── Aer simulator (qiskit-aer package) ────────────────────────────────────────
from qiskit_aer import AerSimulator

# ── IBM Runtime (replaces old qiskit-ibmq-provider) ───────────────────────────
try:
    from qiskit_ibm_runtime import QiskitRuntimeService, Session, SamplerV2 as Sampler
    _IBM_RUNTIME_AVAILABLE = True
except ImportError:
    _IBM_RUNTIME_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Internal: map legacy backend name → AerSimulator method
# ─────────────────────────────────────────────────────────────────────────────
_LEGACY_TO_AER_METHOD: dict[str, str] = {
    "qasm_simulator":        "automatic",
    "statevector_simulator": "statevector",
    "unitary_simulator":     "unitary",
    "aer_simulator":         "automatic",
    "aer_simulator_statevector": "statevector",
    "aer_simulator_unitary":     "unitary",
    "aer_simulator_density_matrix": "density_matrix",
    "aer_simulator_matrix_product_state": "matrix_product_state",
}


def _has_save_instruction(qc) -> bool:
    return any(inst.operation.name.startswith("save_") for inst in qc.data)


class LegacyAerSimulator(AerSimulator):
    """AerSimulator that behaves like the old Aer / BasicAer simulators on ``.run()``.

    * transpiles the circuits first (old ``execute()`` did this, ``AerSimulator.run()`` does not)
    * in ``statevector`` / ``unitary`` mode appends ``save_statevector()`` / ``save_unitary()``
      so ``result.get_statevector()`` / ``result.get_unitary()`` work as before.
    """

    def run(self, circuits, parameter_binds=None, **run_options):
        from qiskit import QuantumCircuit

        single = isinstance(circuits, QuantumCircuit)
        circuit_list = [circuits] if single else list(circuits)
        method = self.options.method
        prepared = []
        for qc in circuit_list:
            if isinstance(qc, QuantumCircuit) and not _has_save_instruction(qc):
                if method == "statevector":
                    qc = qc.copy()
                    qc.save_statevector()
                elif method == "unitary":
                    qc = qc.remove_final_measurements(inplace=False)
                    qc.save_unitary()
            prepared.append(qc)
        # transpile only circuits with instructions Aer cannot run natively (custom gates, ...)
        supported = self.target.operation_names
        try:
            prepared = [qc if all(inst.operation.name in supported for inst in qc.data)
                        else transpile(qc, backend=self) for qc in prepared]
        except Exception:
            pass
        job = super().run(prepared[0] if single else prepared,
                          parameter_binds=parameter_binds, **run_options)
        self._jobs[job.job_id()] = job
        return job

    def retrieve_job(self, job_id):
        """Return a job previously run on this simulator (old IBMQ backend API)."""
        return self._jobs[job_id]

    @property
    def _jobs(self):
        if not hasattr(self, "_job_registry"):
            self._job_registry = {}
        return self._job_registry

    # BackendV1-style helpers still called by the older notebooks
    def status(self):
        from types import SimpleNamespace
        return SimpleNamespace(backend_name=self.name, backend_version=self.backend_version,
                               operational=True, pending_jobs=0, status_msg="active")

    def job_limit(self):
        return None


def get_backend(
    name: str = "qasm_simulator",
    *,
    token: str | None = None,
    instance: str | None = None,
    min_num_qubits: int | None = None,
    **aer_kwargs: Any,
) -> Backend:
    """Return the requested backend.

    Parameters
    ----------
    name : str
        Either a legacy Aer/BasicAer simulator name
        (``'qasm_simulator'``, ``'statevector_simulator'``, ``'unitary_simulator'``)
        or a real IBM Quantum device name (e.g. ``'ibm_brisbane'``).
        Use ``'simulator'`` or ``'aer_simulator'`` for the default local simulator.
    token : str, optional
        IBM Quantum API token.  If omitted, the value of the environment
        variable ``IBM_QUANTUM_TOKEN`` is used, falling back to any
        previously saved account credentials.
    instance : str, optional
        IBM Quantum Platform instance (CRN or name).  Only used for real
        hardware; ``None`` lets the service pick the default instance.
    min_num_qubits : int, optional
        When *name* is ``'least_busy'``, select the least-busy real device
        that has at least this many qubits.
    **aer_kwargs
        Extra keyword arguments forwarded to :class:`~qiskit_aer.AerSimulator`.

    Returns
    -------
    Backend
        A configured backend ready for :func:`transpile` + ``.run()``.
    """
    norm = name.lower().strip()

    # ── Local Aer simulator ───────────────────────────────────────────────────
    if norm in _LEGACY_TO_AER_METHOD or norm in ("simulator",):
        method = _LEGACY_TO_AER_METHOD.get(norm, "automatic")
        return LegacyAerSimulator(method=method, **aer_kwargs)

    # ── Real IBM hardware or least_busy ───────────────────────────────────────
    if not _IBM_RUNTIME_AVAILABLE:
        raise ImportError(
            "qiskit-ibm-runtime is not installed.  "
            "Run: pip install qiskit-ibm-runtime"
        )

    _token = token or os.environ.get("IBM_QUANTUM_TOKEN")
    try:
        if _token:
            service = QiskitRuntimeService(channel="ibm_quantum_platform", token=_token, instance=instance)
        else:
            service = QiskitRuntimeService(instance=instance)
    except Exception as exc:
        raise RuntimeError(
            "Could not connect to IBM Quantum.  "
            "Set the IBM_QUANTUM_TOKEN environment variable or pass token= to get_backend().\n"
            f"Original error: {exc}"
        ) from exc

    if norm == "least_busy":
        backends = service.backends(
            simulator=False,
            operational=True,
            min_num_qubits=min_num_qubits or 1,
        )
        if not backends:
            raise RuntimeError("No suitable IBM Quantum backends found.")
        # sort by queue depth (pending_jobs)
        backends.sort(key=lambda b: b.status().pending_jobs)
        backend = backends[0]
        print(f"[qiskit_backend_config] Using least-busy backend: {backend.name}")
        return backend

    return service.backend(name)


# ─────────────────────────────────────────────────────────────────────────────
# execute() — drop-in replacement for the removed qiskit.execute()
# ─────────────────────────────────────────────────────────────────────────────
class _FakeResult:
    """Thin wrapper that mimics the old qiskit.result.Result interface."""

    def __init__(self, raw_result, circuit_or_circuits, backend):
        self._result = raw_result
        self._circuits = (
            circuit_or_circuits
            if isinstance(circuit_or_circuits, (list, tuple))
            else [circuit_or_circuits]
        )
        self._backend = backend

    # ── measurement counts ────────────────────────────────────────────────────
    def get_counts(self, circuit=None):
        """Return counts dict.  Works for AerSimulator .run() results."""
        # AerSimulator / Qiskit Result object path (primary)
        try:
            if circuit is not None:
                return self._result.get_counts(circuit)
            return self._result.get_counts()
        except Exception:
            pass
        return {}

    def get_statevector(self, *args, **kwargs):
        """Return statevector (Statevector object)."""
        try:
            return self._result.get_statevector(*args, **kwargs)
        except Exception:
            pass
        raise RuntimeError("get_statevector() not available for this backend/result type.")

    def get_unitary(self, *args, **kwargs):
        """Return the unitary matrix."""
        try:
            return self._result.get_unitary(*args, **kwargs)
        except Exception:
            pass
        raise RuntimeError("get_unitary() not available for this backend/result type.")

    def get_memory(self, *args, **kwargs):
        try:
            return self._result.get_memory(*args, **kwargs)
        except Exception:
            return []

    # Delegate everything else to the underlying result
    def __getattr__(self, item):
        return getattr(self._result, item)


def execute(circuits, backend: Backend, shots: int = 1024, **kwargs) -> Any:
    """Drop-in replacement for the removed ``qiskit.execute()``.

    Transpiles *circuits* for *backend* and calls ``backend.run()``.
    Returns an object with the same ``.result()`` interface used in the old API.

    Parameters
    ----------
    circuits : QuantumCircuit | list[QuantumCircuit]
        One or more quantum circuits to run.
    backend : Backend
        A backend returned by :func:`get_backend`.
    shots : int
        Number of measurement shots (ignored for statevector / unitary backends).
    **kwargs
        Extra keyword arguments forwarded to ``backend.run()`` (e.g. ``memory=True``).
    """
    circuit_list = circuits if isinstance(circuits, (list, tuple)) else [circuits]

    # Determine simulator method to adjust shots / save instructions
    method = getattr(backend, "options", None)
    is_statevector = False
    is_unitary = False
    try:
        method_str = backend.options.method if hasattr(backend, "options") else ""
        is_statevector = method_str in ("statevector",) or getattr(backend, "name", "") in (
            "statevector_simulator",
            "aer_simulator_statevector",
        )
        is_unitary = method_str in ("unitary",) or getattr(backend, "name", "") in (
            "unitary_simulator",
            "aer_simulator_unitary",
        )
    except Exception:
        pass

    # Save statevector / unitary so result.get_statevector() / get_unitary() work
    save_circuits = []
    for qc in circuit_list:
        qc2 = qc.copy()
        if is_statevector:
            try:
                qc2.save_statevector()
            except Exception:
                pass
        if is_unitary:
            try:
                qc2 = qc2.remove_final_measurements(inplace=False)
                qc2.save_unitary()
            except Exception:
                pass
        save_circuits.append(qc2)

    # Transpile for the target backend (LegacyAerSimulator.run() does this itself, when needed)
    if isinstance(backend, LegacyAerSimulator):
        t_circuits = save_circuits
    else:
        try:
            t_circuits = transpile(save_circuits, backend=backend)
        except Exception:
            t_circuits = save_circuits

    # Drop kwargs not accepted by AerSimulator.run()
    run_kwargs = {k: v for k, v in kwargs.items() if k in ("shots", "memory", "seed_simulator",
                                                             "noise_model", "basis_gates",
                                                             "coupling_map", "initial_layout")}
    if not (is_statevector or is_unitary):
        run_kwargs.setdefault("shots", shots)

    job = backend.run(t_circuits, **run_kwargs)

    # Wrap the result so .result() returns a _FakeResult
    class _FakeJob:
        def __init__(self, inner_job, circs, bk):
            self._job = inner_job
            self._circuits = circs
            self._backend = bk

        def result(self):
            raw = self._job.result()
            return _FakeResult(raw, self._circuits, self._backend)

        def job_id(self):
            try:
                return self._job.job_id()
            except Exception:
                return "local"

        def status(self):
            try:
                return self._job.status()
            except Exception:
                return "DONE"

        def error_message(self):
            return None

        def __getattr__(self, item):
            return getattr(self._job, item)

    return _FakeJob(job, circuit_list, backend)


# ─────────────────────────────────────────────────────────────────────────────
# Backward-compatible shims:  Aer  and  BasicAer
# ─────────────────────────────────────────────────────────────────────────────
class _AerShim:
    """Shim that replaces ``from qiskit import Aer`` / ``from qiskit_aer import Aer``."""

    @staticmethod
    def get_backend(name: str, **kwargs) -> AerSimulator:
        return get_backend(name, **kwargs)

    @staticmethod
    def backends(name: str | None = None, **kwargs):
        return [
            LegacyAerSimulator(method=m)
            for m in ("automatic", "statevector", "unitary",
                      "density_matrix", "matrix_product_state")
        ]


class _BasicAerShim:
    """Shim that replaces ``from qiskit import BasicAer`` (removed in Qiskit 2.x)."""

    @staticmethod
    def get_backend(name: str, **kwargs) -> AerSimulator:
        warnings.warn(
            "BasicAer is removed in Qiskit 2.x.  "
            "Using AerSimulator as a drop-in replacement.",
            DeprecationWarning,
            stacklevel=2,
        )
        return get_backend(name, **kwargs)

    @staticmethod
    def backends(name: str | None = None, **kwargs):
        return [get_backend(n) for n in ("qasm_simulator", "statevector_simulator", "unitary_simulator")]


#: Drop-in for ``from qiskit import Aer``
Aer = _AerShim()

#: Drop-in for ``from qiskit import BasicAer``
BasicAer = _BasicAerShim()


# ─────────────────────────────────────────────────────────────────────────────
# Backward-compatible shims:  IBMQ, least_busy, job_monitor
# ─────────────────────────────────────────────────────────────────────────────
def _ibm_token() -> str | None:
    return _IBMQShim._token or os.environ.get("IBM_QUANTUM_TOKEN") or None


class _ProviderShim:
    """Stands in for the old ``IBMQ.get_provider()`` provider object.

    Real devices are fetched through ``QiskitRuntimeService`` when a token is
    available; otherwise (or on any connection error) the local simulator is
    returned so the notebook keeps running.
    """

    def get_backend(self, name: str = "qasm_simulator", **kwargs) -> Backend:
        norm = name.lower().strip()
        if "simulator" in norm:
            return get_backend("qasm_simulator")
        if _ibm_token():
            try:
                return get_backend(name, token=_ibm_token())
            except Exception as exc:
                warnings.warn(f"Could not get IBM backend {name!r} ({exc}); using the local simulator.")
        else:
            warnings.warn(f"No IBM Quantum token set; using the local simulator instead of {name!r}.")
        return get_backend("qasm_simulator")

    def backends(self, name: str | None = None, filters=None, **kwargs):
        if name:
            return [self.get_backend(name)]
        if _ibm_token():
            try:
                service = QiskitRuntimeService(channel="ibm_quantum_platform", token=_ibm_token())
                kwargs.pop("n_qubits", None)
                backends = service.backends(**{k: v for k, v in kwargs.items()
                                               if k in ("simulator", "operational", "min_num_qubits")})
                return [b for b in backends if filters is None or filters(b)]
            except Exception as exc:
                warnings.warn(f"Could not list IBM backends ({exc}); using the local simulator.")
        return [get_backend("qasm_simulator")]


class _IBMQShim:
    """Shim that replaces ``from qiskit import IBMQ`` (removed with qiskit-ibmq-provider)."""

    _token: str | None = None

    def enable_account(self, token: str | None = None, *args, **kwargs):
        if token:
            _IBMQShim._token = token
        return _ProviderShim()

    def save_account(self, token: str | None = None, *args, **kwargs):
        if token:
            _IBMQShim._token = token

    def load_account(self, *args, **kwargs):
        return _ProviderShim()

    # qiskit-ibmq-provider < 0.4 API
    def load_accounts(self, *args, **kwargs):
        return _ProviderShim()

    def stored_account(self):
        return self.active_account()

    def backends(self, *args, **kwargs):
        return _ProviderShim().backends(*args, **kwargs)

    def get_backend(self, *args, **kwargs):
        return _ProviderShim().get_backend(*args, **kwargs)

    def disable_account(self, *args, **kwargs):
        _IBMQShim._token = None

    def get_provider(self, *args, **kwargs):
        return _ProviderShim()

    def providers(self, *args, **kwargs):
        return [_ProviderShim()]

    def active_account(self):
        return {"token": _ibm_token()} if _ibm_token() else None


#: Drop-in for ``from qiskit import IBMQ``
IBMQ = _IBMQShim()


def least_busy(backends):
    """Drop-in for ``qiskit.providers.ibmq.least_busy``."""
    backends = list(backends)

    def pending(b):
        try:
            return b.status().pending_jobs
        except Exception:
            return 0

    return min(backends, key=pending)


# ─────────────────────────────────────────────────────────────────────────────
# get_runtime_service() — QiskitRuntimeService with a local fallback
# ─────────────────────────────────────────────────────────────────────────────
def _fake_backend(name: str):
    """Return the qiskit_ibm_runtime fake twin of an IBM device, e.g. 'ibm_kyoto' -> FakeKyoto()."""
    from qiskit_ibm_runtime import fake_provider

    cls = getattr(fake_provider, "Fake" + name.split("_", 1)[-1].capitalize(), None)
    if cls is None:
        warnings.warn(f"No fake twin for {name!r}; using FakeSherbrooke (127 qubits).")
        cls = fake_provider.FakeSherbrooke
    return cls()


class _LocalRuntimeService:
    """Stands in for ``QiskitRuntimeService`` when no IBM Quantum account is available.

    Device names resolve to their fake twins, which the V2 primitives
    (``SamplerV2(mode=backend)`` / ``EstimatorV2(mode=backend)``) run locally on Aer.
    """

    def backend(self, name: str = "ibm_sherbrooke", *args, **kwargs):
        return _fake_backend(name)

    get_backend = backend

    def least_busy(self, *args, **kwargs):
        return _fake_backend("ibm_sherbrooke")

    def backends(self, *args, **kwargs):
        return [_fake_backend(n) for n in ("ibm_sherbrooke", "ibm_kyoto", "ibm_osaka", "ibm_torino")]

    def job(self, job_id: str):
        raise RuntimeError(f"Job {job_id!r} lives on IBM Quantum; it cannot be retrieved without an account.")

    def jobs(self, *args, **kwargs):
        return []


class _RuntimeServiceProxy:
    """Real ``QiskitRuntimeService``; retired devices fall back to their fake twins."""

    def __init__(self, service):
        self._service = service

    def backend(self, name: str, *args, **kwargs):
        try:
            return self._service.backend(name, *args, **kwargs)
        except Exception as exc:
            warnings.warn(f"IBM backend {name!r} is unavailable ({exc}); using its fake twin instead.")
            return _fake_backend(name)

    get_backend = backend

    def __getattr__(self, item):
        return getattr(self._service, item)


def get_runtime_service(*args, channel: str | None = None, **kwargs):
    """Drop-in for ``QiskitRuntimeService(...)`` that keeps notebooks runnable without an account.

    * ``channel='ibm_quantum'`` (closed in 2025) is mapped to ``'ibm_quantum_platform'``
    * a token from ``IBM_QUANTUM_TOKEN`` is used when none is passed
    * with no usable account a local service backed by fake devices is returned
    """
    if not _IBM_RUNTIME_AVAILABLE:
        return _LocalRuntimeService()
    if channel == "ibm_quantum":
        channel = "ibm_quantum_platform"
    if "token" not in kwargs and os.environ.get("IBM_QUANTUM_TOKEN"):
        kwargs["token"] = os.environ["IBM_QUANTUM_TOKEN"]
        channel = channel or "ibm_quantum_platform"
    if str(kwargs.get("token", "")).startswith("<"):  # placeholder like '<MY_IBM_QUANTUM_TOKEN>'
        kwargs.pop("token")
    try:
        service = QiskitRuntimeService(*args, channel=channel, **kwargs) if channel \
            else QiskitRuntimeService(*args, **kwargs)
        return _RuntimeServiceProxy(service)
    except Exception as exc:
        print(f"[qiskit_backend_config] No IBM Quantum account ({type(exc).__name__}); "
              "using a local runtime service with fake backends.")
        return _LocalRuntimeService()


def combine(left, right):
    """Drop-in for the removed ``left + right`` / ``left += right`` on QuantumCircuit.

    Like the old operator, registers of *right* missing from *left* are added,
    then *right*'s instructions are appended onto the matching bits.
    """
    out = left.copy()
    for reg in right.qregs:
        if reg not in out.qregs:
            out.add_register(reg)
    for reg in right.cregs:
        if reg not in out.cregs:
            out.add_register(reg)
    out.compose(right, qubits=right.qubits, clbits=right.clbits, inplace=True)
    return out


def assemble(experiments, *args, **kwargs):
    """Drop-in for the removed ``qiskit.assemble()``: backends now run circuits directly."""
    return experiments


def job_monitor(job, *args, **kwargs):
    """Drop-in for ``qiskit.tools.monitor.job_monitor`` (waits for the job to finish)."""
    try:
        job.result()
        print(f"Job Status: {job.status()}")
    except Exception as exc:
        print(f"Job Status: failed ({exc})")


# ─────────────────────────────────────────────────────────────────────────────
# Quick self-test (run as a script)
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from qiskit import QuantumCircuit

    print("=== qiskit_backend_config self-test ===")
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])

    print("\n1. get_backend('qasm_simulator'):", get_backend("qasm_simulator"))
    print("2. Aer.get_backend('qasm_simulator'):", Aer.get_backend("qasm_simulator"))
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        print("3. BasicAer.get_backend('qasm_simulator'):", BasicAer.get_backend("qasm_simulator"))

    backend = get_backend("qasm_simulator")
    job = execute(qc, backend, shots=1024)
    result = job.result()
    print("\n4. execute() counts:", result.get_counts())

    sv_backend = get_backend("statevector_simulator")
    qc_sv = QuantumCircuit(2)
    qc_sv.h(0)
    qc_sv.cx(0, 1)
    job_sv = execute(qc_sv, sv_backend)
    result_sv = job_sv.result()
    print("5. get_statevector():", result_sv.get_statevector())

    print("\nAll tests passed.")
