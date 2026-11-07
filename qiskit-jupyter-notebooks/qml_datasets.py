"""
qml_datasets.py
===============
Shared dataset helpers for the quantum machine learning (QML) notebooks in this repo.

Qiskit Aqua used to ship ``qiskit.ml.datasets`` with ready-made toy datasets for quantum
classifiers (QSVM, VQC, ...). Aqua was removed; only ``ad_hoc_data`` survived (now in
``qiskit_machine_learning.datasets``). This module rebuilds the others with scikit-learn so
the notebooks keep the same API.

Usage
-----
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath('__file__')))
    from qml_datasets import qdatasets, describe_dataset

    data = qdatasets.iris(training_size=10, test_size=4, n=2, plot_data=True)
    describe_dataset(data)

Every dataset function returns the tuple ``(sample_train, training_input, test_input, class_labels)``:

* ``sample_train``   - all training samples, shape ``(num_samples, n)``
* ``training_input`` - dict ``{class_label: array of training samples}``
* ``test_input``     - dict ``{class_label: array of test samples}``
* ``class_labels``   - list of class names, e.g. ``['A', 'B']``
"""

import numpy as np
import matplotlib.pyplot as plt
from sklearn import datasets as skdatasets
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from qiskit_machine_learning.datasets import ad_hoc_data as _qiskit_ad_hoc_data


class qdatasets:
    """The datasets of the removed qiskit.ml.datasets, rebuilt with scikit-learn.

    Classical datasets are prepared as Aqua did: standardise, PCA to ``n`` features,
    scale to [-1, 1], then keep ``training_size`` / ``test_size`` samples per class."""

    @staticmethod
    def _prepare(data, target, training_size, test_size, n, class_labels, split, random_state, plot_data, title):
        x_train, x_test, y_train, y_test = train_test_split(data, target, test_size=split, random_state=random_state)
        # 1. standardise: every feature gets mean 0 and variance 1
        std = StandardScaler().fit(x_train)
        x_train, x_test = std.transform(x_train), std.transform(x_test)
        # 2. PCA: keep only the n most informative directions (one per qubit later on)
        pca = PCA(n_components=n).fit(x_train)
        x_train, x_test = pca.transform(x_train), pca.transform(x_test)
        # 3. scale to [-1, 1] so the values can be used as rotation angles in a feature map
        minmax = MinMaxScaler((-1, 1)).fit(np.append(x_train, x_test, axis=0))
        x_train, x_test = minmax.transform(x_train), minmax.transform(x_test)
        classes = np.unique(target)
        training_input = {class_labels[k]: x_train[y_train == c][:training_size] for k, c in enumerate(classes)}
        test_input = {class_labels[k]: x_test[y_test == c][:test_size] for k, c in enumerate(classes)}
        if plot_data:
            for label, samples in training_input.items():
                plt.scatter(samples[:, 0], samples[:, 1], label=label)
            plt.legend()
            plt.title(title)
            plt.show()
        return x_train, training_input, test_input, class_labels

    @staticmethod
    def ad_hoc_data(training_size, test_size, n, gap, plot_data=False):
        """Ad hoc dataset of Havlicek et al. (Nature 567, 209 (2019)), in the old dictionary format.

        n is 2 or 3; gap (below 1) is the margin kept free between the two classes."""
        x_train, y_train, x_test, y_test = _qiskit_ad_hoc_data(training_size, test_size, n, gap,
                                                               plot_data=plot_data, one_hot=False)
        class_labels = ['A', 'B']
        training_input = {class_labels[c]: x_train[y_train == c] for c in (0, 1)}
        test_input = {class_labels[c]: x_test[y_test == c] for c in (0, 1)}
        return x_train, training_input, test_input, class_labels

    @staticmethod
    def breast_cancer(training_size, test_size, n, plot_data=False):
        """Wisconsin breast cancer: 569 samples, 30 features, 2 classes (malignant / benign)."""
        data, target = skdatasets.load_breast_cancer(return_X_y=True)
        return qdatasets._prepare(data, target, training_size, test_size, n, ['A', 'B'],
                                  0.3, 109, plot_data, 'PCA dim. reduced Breast cancer dataset')

    @staticmethod
    def digits(training_size, test_size, n, plot_data=False):
        """Handwritten digits: 1797 8x8 images (64 features), 10 classes (0-9)."""
        data, target = skdatasets.load_digits(return_X_y=True)
        return qdatasets._prepare(data, target, training_size, test_size, n, [str(d) for d in range(10)],
                                  0.3, 22, plot_data, 'PCA dim. reduced Digits dataset')

    @staticmethod
    def iris(training_size, test_size, n, plot_data=False):
        """Iris flowers: 150 samples, 4 features, 3 classes (species)."""
        data, target = skdatasets.load_iris(return_X_y=True)
        return qdatasets._prepare(data, target, training_size, test_size, n, ['A', 'B', 'C'],
                                  0.3, 42, plot_data, 'Iris dataset')

    @staticmethod
    def wine(training_size, test_size, n, plot_data=False):
        """Wine: 178 samples, 13 chemical features, 3 classes (cultivars)."""
        data, target = skdatasets.load_wine(return_X_y=True)
        return qdatasets._prepare(data, target, training_size, test_size, n, ['A', 'B', 'C'],
                                  0.1, 7, plot_data, 'PCA dim. reduced Wine dataset')

    @staticmethod
    def gaussian(training_size, test_size, n, plot_data=False, seed=7):
        """Two Gaussian clusters in n dimensions (synthetic)."""
        rng = np.random.default_rng(seed)
        # half of the samples go to the test split, so draw twice as many as needed per class
        size = 2 * (training_size + test_size)
        data = np.vstack([rng.normal(-0.5, 0.3, (size, n)), rng.normal(0.5, 0.3, (size, n))])
        target = np.repeat([0, 1], size)
        return qdatasets._prepare(data, target, training_size, test_size, n, ['A', 'B'],
                                  0.5, seed, plot_data, 'Gaussian dataset')


def describe_dataset(data):
    """Print the shape of a (sample_train, training_input, test_input, class_labels) tuple."""
    sample_train, training_input, test_input, class_labels = data
    print(f'class labels : {class_labels}')
    print(f'sample_train : {sample_train.shape[0]} samples x {sample_train.shape[1]} features')
    for label in class_labels:
        print(f'  class {label!r:5}: {len(training_input[label]):3} training, {len(test_input[label]):3} test samples')
