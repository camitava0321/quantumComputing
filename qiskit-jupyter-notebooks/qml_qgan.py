"""
qml_qgan.py
===========
Small helpers for the 42x-QGAN notebooks (quantum generative adversarial networks).

A qGAN (Zoufal, Lucchi, Woerner, "Quantum Generative Adversarial Networks for learning and
loading random distributions", npj Quantum Information 5, 103 (2019)) has two players:

* a **quantum generator** - a parameterised circuit on n qubits.  Measuring it gives one of the
  2^n basis states, and each basis state stands for one point of a grid laid over the data, so
  the circuit *is* a probability distribution p_theta over that grid;
* a **classical discriminator** - a small neural network D(x) in [0, 1] that tries to tell real
  data points (label 1) from generated ones (label 0).

The generator is a qiskit-machine-learning ``SamplerQNN`` wrapped in a ``TorchConnector`` so that
PyTorch can train it together with the discriminator.  This is the modern replacement for the
``QGAN`` class that used to live in Qiskit Aqua.

Notebook 421 writes every step out by hand; the later notebooks import these functions so they
can focus on the data.
"""

from __future__ import annotations

import numpy as np
import torch
from torch import nn
from scipy.stats import entropy

from qiskit import QuantumCircuit
from qiskit.circuit.library import efficient_su2, real_amplitudes
from qiskit.primitives import StatevectorSampler
from qiskit_machine_learning.connectors import TorchConnector
from qiskit_machine_learning.gradients import ParamShiftSamplerGradient
from qiskit_machine_learning.neural_networks import SamplerQNN


# ─────────────────────────────────────────────────────────────────────────────
# Data: snap samples onto the grid the generator can represent
# ─────────────────────────────────────────────────────────────────────────────
def discretize(data, bounds, num_qubits):
    """Turn raw samples into a probability distribution over the generator's grid.

    data        : array (N,) or (N, k) of samples
    bounds      : [[min_0, max_0], ..., [min_k-1, max_k-1]]  (a single [min, max] for k = 1)
    num_qubits  : qubits per dimension, e.g. [3] or [2, 2]

    Returns ``(grid_elements, prob_data)``: ``grid_elements[i]`` is the data point represented by
    basis state |i>, and ``prob_data[i]`` the fraction of samples that fall closest to it.
    Basis state |i> uses its lowest ``num_qubits[0]`` bits for dimension 0, the next
    ``num_qubits[1]`` bits for dimension 1, and so on (Qiskit's little-endian convention).
    Samples outside ``bounds`` are dropped.
    """
    data = np.asarray(data, dtype=float).reshape(len(data), -1)
    bounds = np.asarray(bounds, dtype=float).reshape(data.shape[1], 2)
    inside = np.all((data >= bounds[:, 0]) & (data <= bounds[:, 1]), axis=1)
    data = data[inside]

    axes = [np.linspace(lo, hi, 2 ** n) for (lo, hi), n in zip(bounds, num_qubits)]
    # index of the nearest grid value in every dimension
    idx = [np.abs(data[:, j, None] - axis[None, :]).argmin(axis=1) for j, axis in enumerate(axes)]
    offsets = np.cumsum([0] + list(num_qubits[:-1]))
    basis_index = sum(i << int(o) for i, o in zip(idx, offsets))

    prob_data = np.bincount(basis_index, minlength=2 ** sum(num_qubits)) / len(data)
    grid_elements = np.array([[axes[j][(i >> int(offsets[j])) & (2 ** n - 1)]
                               for j, n in enumerate(num_qubits)]
                              for i in range(2 ** sum(num_qubits))])
    return grid_elements, prob_data


# ─────────────────────────────────────────────────────────────────────────────
# Generator
# ─────────────────────────────────────────────────────────────────────────────
def generator_circuit(num_qubits, reps=2, ansatz="efficient_su2"):
    """Hadamards (start from the uniform distribution) followed by a trainable ansatz."""
    n = int(np.sum(num_qubits))
    qc = QuantumCircuit(n)
    qc.h(range(n))
    if ansatz == "efficient_su2":
        qc.compose(efficient_su2(n, reps=reps), inplace=True)
    elif ansatz == "real_amplitudes":
        qc.compose(real_amplitudes(n, reps=reps), inplace=True)
    else:
        raise ValueError(f"unknown ansatz {ansatz!r}")
    return qc


def make_generator(circuit, shots=2_000, seed=42, initial_weights=None):
    """Wrap ``circuit`` as a PyTorch module whose output is the vector of 2^n probabilities.

    The probabilities are estimated from ``shots`` measurements.  2000 shots keeps training fast
    (the run time grows with the shot count) at a statistical error of about 1%.
    """
    sampler = StatevectorSampler(default_shots=shots, seed=seed)
    qnn = SamplerQNN(circuit=circuit, sampler=sampler, input_params=[],
                     weight_params=circuit.parameters, sparse=False,
                     gradient=ParamShiftSamplerGradient(sampler))
    if initial_weights is None:
        initial_weights = np.random.default_rng(seed).random(qnn.num_weights)
    return TorchConnector(qnn, initial_weights=initial_weights)


# ─────────────────────────────────────────────────────────────────────────────
# Discriminator
# ─────────────────────────────────────────────────────────────────────────────
class Discriminator(nn.Module):
    """k -> 20 -> 1 network with a leaky ReLU hidden layer and a sigmoid output."""

    def __init__(self, input_size, hidden=20):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(input_size, hidden), nn.LeakyReLU(0.2),
                                 nn.Linear(hidden, 1), nn.Sigmoid())

    def forward(self, x):
        return self.net(x)


def adversarial_loss(prediction, target, weight):
    """Binary cross entropy where every grid point is weighted by its probability."""
    prediction = prediction.clamp(1e-7, 1 - 1e-7)
    bce = target * torch.log(prediction) + (1 - target) * torch.log(1 - prediction)
    return -torch.sum(weight * bce)


# ─────────────────────────────────────────────────────────────────────────────
# Training
# ─────────────────────────────────────────────────────────────────────────────
def train_qgan(generator, discriminator, grid_elements, prob_data, num_epochs=150,
               lr_generator=0.02, lr_discriminator=0.05, d_steps=3, callback=None):
    """Per epoch: one generator step, then ``d_steps`` discriminator steps.

    Giving the discriminator a higher learning rate and several steps keeps it close to its
    optimum, so the generator always follows a meaningful signal; with equal rates and a single
    step the two networks tend to chase each other in circles instead of converging.

    Returns a dict of per-epoch lists: ``g_loss``, ``d_loss`` and ``rel_entr`` (the
    Kullback-Leibler divergence between generated and data distribution - 0 means identical).
    ``callback(epoch, history)`` is called after every epoch, e.g. to draw live plots.
    """
    # scale the grid to [0, 1] per dimension so the discriminator sees well-conditioned inputs
    lo, hi = grid_elements.min(axis=0), grid_elements.max(axis=0)
    samples = torch.tensor((grid_elements - lo) / np.where(hi > lo, hi - lo, 1), dtype=torch.float)
    real_prob = torch.tensor(prob_data, dtype=torch.float).reshape(-1, 1)
    valid = torch.ones(len(samples), 1)
    fake = torch.zeros(len(samples), 1)

    opt_g = torch.optim.Adam(generator.parameters(), lr=lr_generator, betas=(0.7, 0.999))
    opt_d = torch.optim.Adam(discriminator.parameters(), lr=lr_discriminator, betas=(0.7, 0.999))
    history = {"g_loss": [], "d_loss": [], "rel_entr": []}

    for epoch in range(num_epochs):
        gen_prob = generator(torch.tensor([])).reshape(-1, 1)

        # generator: make D call generated points "real"
        opt_g.zero_grad()
        g_loss = adversarial_loss(discriminator(samples), valid, gen_prob)
        g_loss.backward(retain_graph=True)
        opt_g.step()

        # discriminator: real points -> 1, generated points -> 0
        for _ in range(d_steps):
            opt_d.zero_grad()
            d_loss = (adversarial_loss(discriminator(samples), valid, real_prob)
                      + adversarial_loss(discriminator(samples), fake, gen_prob.detach())) / 2
            d_loss.backward()
            opt_d.step()

        history["g_loss"].append(g_loss.item())
        history["d_loss"].append(d_loss.item())
        history["rel_entr"].append(relative_entropy(gen_prob.detach().numpy().ravel(), prob_data))
        if callback is not None:
            callback(epoch, history)
    return history


def generated_distribution(generator):
    """Current output distribution of the generator as a NumPy array."""
    with torch.no_grad():
        return generator(torch.tensor([])).numpy().ravel()


def relative_entropy(p_generated, p_data):
    """KL divergence D(p_generated || p_data); a tiny epsilon avoids log(0)."""
    return float(entropy(np.asarray(p_generated) + 1e-10, np.asarray(p_data) + 1e-10))


# ─────────────────────────────────────────────────────────────────────────────
# Plotting
# ─────────────────────────────────────────────────────────────────────────────
def plot_history(history, title=""):
    """Loss curves and relative entropy side by side."""
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    ax1.plot(history["g_loss"], label="generator", color="mediumvioletred", lw=2)
    ax1.plot(history["d_loss"], label="discriminator", color="rebeccapurple", lw=2)
    ax1.set(title=f"{title} loss".strip(), xlabel="epoch", ylabel="loss")
    ax1.legend()
    ax1.grid(alpha=0.3)
    ax2.plot(history["rel_entr"], color="mediumblue", lw=2)
    ax2.set(title=f"{title} relative entropy".strip(), xlabel="epoch", ylabel="KL divergence")
    ax2.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()


def grid_labels(grid_elements, fmt="{:.3g}"):
    """Readable x-tick labels for the grid points, e.g. '(1.5, 2)'."""
    if grid_elements.shape[1] == 1:
        return [fmt.format(v) for v in grid_elements[:, 0]]
    return ["(" + ", ".join(fmt.format(v) for v in row) + ")" for row in grid_elements]


__all__ = ["discretize", "generator_circuit", "make_generator", "Discriminator",
           "adversarial_loss", "train_qgan", "generated_distribution", "relative_entropy",
           "plot_history", "grid_labels"]
