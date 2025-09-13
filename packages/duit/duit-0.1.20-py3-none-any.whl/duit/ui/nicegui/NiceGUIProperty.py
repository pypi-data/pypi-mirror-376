from abc import ABC
from typing import Generic, Optional

from duit.model.DataField import T
from duit.ui.BaseProperty import BaseProperty, M
from duit.ui.annotations import UIAnnotation


class NiceGUIProperty(Generic[T, M], BaseProperty[T, M], ABC):
    """
    A generic property class for NiceGUI that extends BaseProperty.

    This class is designed to manage properties that are tied to UI annotations and models.

    :typeparam T: The type of the value managed by the property.
    :typeparam M: The type of the data model associated with the property.
    """

    def __init__(self, annotation: UIAnnotation, model: Optional[M] = None):
        """
        Initializes a NiceGUIProperty.

        :param annotation: The UI annotation associated with this property.
        :param model: An optional data model instance linked with the property.
        """
        super().__init__(annotation, model)
