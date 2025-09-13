from __future__ import annotations

from dataclasses import dataclass, field

from duit.model.DataField import DataField
from duit.ui.annotations import UIAnnotation


@dataclass
class MetaNode:
    """
    A generic node in the property tree.

    This class represents a hierarchical structure used for UI modeling:
    - If `annotation` is a `StartSection` or `SubSection`, `children` contains nested `MetaNode` instances.
    - Otherwise, the node is treated as a leaf and may be bound to a specific data model field.

    :param name: The name identifier of the node.
    :param annotation: The UI annotation describing this node's role or type.
    :param model: An optional data field model associated with this node.
    :param children: A list of child nodes if this node represents a section.
    """
    name: str
    annotation: UIAnnotation
    model: DataField | None = None
    children: list[MetaNode] = field(default_factory=list)

    def __repr__(self):
        """
        Returns a string representation of the MetaNode object for debugging.

        :returns: A string representation using __str__.
        """
        return self.__str__()

    def __str__(self):
        """
        Constructs a concise string description of the MetaNode.

        :returns: A formatted string with the node's name and annotation type.
        """
        return f"MetaNode({self.name}, {type(self.annotation).__name__}"
