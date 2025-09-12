import torch
import torch.nn as nn

from hyptorch.models.base import HyperbolicMobiusModel


class HyperbolicLayer(nn.Module):
    """
    Base class for hyperbolic neural network layers.

    This abstract class provides a foundation for all hyperbolic layers,
    maintaining a reference to the underlying hyperbolic manifold and
    providing convenient access to its curvature.

    Parameters
    ----------
    model : HyperbolicMobiusModel
        The hyperbolic model on which the layer operates.

    Attributes
    ----------
    model : HyperbolicMobiusModel
        The hyperbolic model instance.
    curvature : torch.Tensor
        The curvature of the model (accessible via property).

    Notes
    -----
    All hyperbolic layers should inherit from this base class to ensure
    consistent handling of the model and its properties.
    """

    def __init__(self, model: HyperbolicMobiusModel):
        super().__init__()
        self.model = model

    @property
    def curvature(self) -> torch.Tensor:
        """
        Get the curvature parameter of the hyperbolic model.

        Returns
        -------
        torch.Tensor
            The curvature parameter as a tensor.
        """
        return self.model.curvature
