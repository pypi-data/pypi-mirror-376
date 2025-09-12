"""Abstract class for Multi-Armed Bandit algorithms.

This class defines the interface for MAB algorithms to be used in the GOBRec
recommender system. It also includes a label encoder to handle item IDs.
"""
from abc import ABC, abstractmethod
import numpy as np
from typing import Union
import torch


class _LabelEncoder:
    """A simple label encoder to convert item IDs to integer indices and vice versa.

    Different from sklearn's LabelEncoder, this implementation can be updated with new
    classes after fitting. This is useful for MAB algorithms where new items may appear
    over time.

    Attributes
    ----------
    class_to_index : dict[Union[str, int], int]
        A mapping from item IDs, which can be strings or integers, to integer indices.
    index_to_class : list[Union[str, int]]
        A list mapping integer indices back to item IDs.
    """

    def __init__(self):
        """Initialize the label encoder."""
        self.class_to_index: dict[Union[str, int], int] = {}
        self.index_to_class: list[Union[str, int]] = []

    def fit(self, decisions: np.ndarray):
        """Fit the label encoder with the provided item IDs.

        New item IDs will be added to the existing mapping.
        Different from sklearn.label_encoder, this method can
        be called multiple times to update the mapping.

        Parameters
        ----------
        decisions : np.ndarray
            A 1D array of item IDs, which can be strings or integers.
        """
        for cls in decisions:
            if cls not in self.class_to_index:
                idx = len(self.index_to_class)
                self.class_to_index[cls] = idx
                self.index_to_class.append(cls)

    def transform(self, decisions: np.ndarray) -> np.ndarray:
        """Transform item IDs to encoded integer indices.

        Parameters
        ----------
        decisions : np.ndarray
            A 1D array of item IDs, which can be strings or integers.
        
        Returns
        -------
        indices : np.ndarray
            A 1D array of integer indices corresponding to the item IDs.
        """
        return np.array([self.class_to_index[cls] for cls in decisions])

    def inverse_transform(self, indices: np.ndarray) -> np.ndarray:
        """Transform encoded integer indices back to item IDs.

        Parameters
        ----------
        indices : np.ndarray
            A 1D array of integer indices.
        
        Returns
        -------
        item_ids : np.ndarray
            A 1D array of item IDs corresponding to the integer indices.
        """
        return np.array([self.index_to_class[idx] for idx in indices])

    @property
    def classes_(self):
        """Array of item IDs known to the encoder."""
        return np.array(self.index_to_class)


class MABAlgo(ABC):
    """Abstract class for Multi-Armed Bandit algorithms.

    This class defines the interface for MAB algorithms to be used in the GOBRec
    recommender system. It also includes commom label encoding functionality to handle
    item IDs.

    Attributes
    ----------
    seed : int
        Random seed for reproducibility.
    rng : np.random.Generator
        Random number generator, initialized with the provided seed.
    label_encoder : _LabelEncoder
        A label encoder to convert item IDs to integer indices and vice versa.
    num_arms : int
        The number of unique arms (items) known to the algorithm. It starts as None and
        is updated when fitting with new item IDs.
    num_features : int
        The number of features in the context vectors. It starts as None and is set
        when fitting for the first time. It is asserted to be consistent in subsequent
        fits.
    """

    def __init__(self, seed: int = None):
        """Initialize the MAB algorithm.

        Parameters
        ----------
        seed : int, optional
            Random seed for reproducibility. Default is None.
        """
        self.seed = seed
        self.rng = np.random.default_rng(self.seed)
        self.label_encoder = None
        self.num_arms = None
        self.num_features = None
    
    def _update_label_encoder(self, decisions: np.ndarray, num_features: int):
        """Update the label encoder with new item IDs if any.

        It also sets the new number of arms and checks for consistency in the
        number of features. It is recommended to call this method at the beginning
        of the `fit` method of subclasses.

        Parameters
        ----------
        decisions : np.ndarray
            A 1D array of item IDs, which can be strings or integers.
        num_features : int
            The number of features in the context vectors.
        """
        if self.label_encoder is None:
            self.label_encoder = _LabelEncoder()
        self.label_encoder.fit(decisions)
        self.num_arms = len(self.label_encoder.classes_)
        
        if self.num_features is None:
            self.num_features = num_features
        
        assert num_features == self.num_features, "Number of features has changed!"
        

    @abstractmethod
    def fit(self, contexts: np.ndarray, decisions: np.ndarray, rewards: np.ndarray):
        """Fit the MAB algorithm with the provided contexts, item IDs, and rewards.

        Parameters
        ----------
        contexts : np.ndarray
            A 2D array of shape (n_samples, n_features) representing the context arrays.
        decisions : np.ndarray
            A 1D array of item IDs (arms or decisions) of shape (n_samples,)
            where each element can be strings or integers.
        rewards : np.ndarray
            A 1D array of rewards (ratings) of shape (n_samples,). It can be integers
            or floats.
        """
        pass

    @abstractmethod
    def predict(self, contexts: np.ndarray) -> torch.Tensor:
        """Predict the expected rewards for the given contexts.

        Parameters
        ----------
        contexts : np.ndarray
            A 2D array of shape (n_samples, n_features) representing the context arrays
        
        Returns
        -------
        expected_rewards : torch.Tensor
            A 2D tensor of shape (n_samples, n_arms) representing the expected
            rewards for each arm (item) given the contexts. The encoded items
            ids are used here. To get the original item IDs, it is possible to
            use the `label_encoder.inverse_transform` method.
        """
        pass

    @abstractmethod
    def reset(self):
        """Reset the MAB algorithm to its initial state.

        This method should clear any learned parameters and reinitialize the
        random number generator with the original seed.

        This will make the algorithm behave as if it was just initialized.
        """
        self.label_encoder = None
        self.num_arms = None
        self.num_features = None
        self.rng = np.random.default_rng(self.seed)