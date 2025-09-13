from typing import Any, Sequence

from duit.collections.Stack import Stack
from duit.ui.annotations import find_all_ui_annotations
from duit.ui.annotations.TitleAnnoation import TitleAnnotation
from duit.ui.annotations.container.EndSectionAnnotation import EndSectionAnnotation
from duit.ui.annotations.container.StartSectionAnnotation import StartSectionAnnotation
from duit.ui.annotations.container.SubSectionAnnotation import SubSectionAnnotation
from duit.ui.meta.MetaNode import MetaNode


def build_meta_tree(obj: Any) -> list[MetaNode]:
    """
    Constructs a hierarchical MetaNode tree from the UI annotations of an object.

    This function traverses all UI annotations associated with the object and
    constructs a tree representation based on section annotations. Each field
    or nested section becomes a node in the tree.

    - `StartSectionAnnotation` and `SubSectionAnnotation` begin new sections.
    - `EndSectionAnnotation` closes the current section.
    - Other annotations are treated as leaf nodes.

    :param obj: The object containing UI-annotated fields.

    :returns: A list of MetaNode objects representing the root-level children.
    """
    root = MetaNode(name="root", annotation=TitleAnnotation())
    stack: Stack[MetaNode] = Stack()
    stack.push(root)

    # find_all_ui_annotations returns a dict in insertion order
    annotations = find_all_ui_annotations(obj)

    for var_name, (model, anns) in annotations.items():
        # sort the per-field annotations to keep deterministic
        sorted_anns = sorted(anns)

        for ann in sorted_anns:
            if isinstance(ann, StartSectionAnnotation):
                node = MetaNode(name=ann.name, annotation=ann)
                stack.peek().children.append(node)

                if isinstance(ann, SubSectionAnnotation):
                    sub_tree = build_meta_tree(model.value)
                    node.children.extend(sub_tree)
                    continue

                stack.push(node)
                continue

            if isinstance(ann, EndSectionAnnotation):
                if stack.is_empty:
                    raise Exception(f"Unmatched EndSectionAnnotation on {var_name}")

                stack.pop()
                continue

            # add regular field annotation
            node = MetaNode(name=ann.name, annotation=ann, model=model)
            stack.peek().children.append(node)

    return root.children


def generate_meta_tree_str(
        node_or_nodes: MetaNode | Sequence[MetaNode],
        indent_str: str = "    ",
        level: int = 0
) -> str:
    """
    Generates a string representation of a MetaNode tree with indentation.

    Useful for visualizing the hierarchy of UI annotations in a tree format.

    :param node_or_nodes: A single MetaNode or a sequence (list/tuple) of MetaNodes.
    :param indent_str: The string used to indent each level (default is four spaces).
    :param level: The current recursion level (used internally for indentation).

    :returns: A string containing the formatted tree structure.
    """
    lines: list[str] = []

    # normalize to a sequence
    nodes = node_or_nodes if isinstance(node_or_nodes, Sequence) else [node_or_nodes]

    for node in nodes:
        # line for this node
        lines.append(f"{indent_str * level}{node.name} ({type(node.annotation).__name__})")
        # recurse into children
        if node.children:
            lines.append(generate_meta_tree_str(node.children, indent_str, level + 1))

    return "\n".join(lines)
