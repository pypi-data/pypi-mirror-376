from typing import Any, Dict, Optional
from rich.console import Console
from rich.tree import Tree
import inspect

def safe_getattr(obj: Any, name: str) -> Optional[Any]:
    """Safely get an attribute, returning None if not accessible."""
    try:
        return getattr(obj, name)
    except Exception:
        return None

def classify_members(
    obj: Any,
    all_attributes: set,
    condition,
) -> Dict[str, Any]:
    """
    Helper to classify object members.

    Args:
        obj (Any): Object being inspected.
        all_attributes (set): Names left to classify.
        condition (Callable[[str, Any], bool]): Function deciding inclusion.

    Returns:
        Dict[str, Any]: Ordered mapping of name -> attribute value.
    """
    result: Dict[str, Any] = {}
    for name in sorted(all_attributes):
        val = safe_getattr(obj, name)
        if condition(name, val):
            result[name] = val
            all_attributes.discard(name)
    return result

def map_object(obj: Any) -> Dict[str, Any]:
    """
    Generate a structured introspection map of a Python object.

    Args:
        obj (Any): The object to analyze.

    Returns:
        Dict[str, Any]: A structured dictionary of the object’s metadata.
    """
    obj_map: Dict[str, Any] = {
        "type_info": {"type": type(obj), "id": id(obj)},
        "class_info": {"class": obj.__class__, "bases": obj.__class__.__bases__},
        "magic_methods": {},
        "methods_internal": {},
        "methods_external": {},
        "attributes_internal": {},
        "attributes_external": {},
        "properties": {},
        "others": {},
    }

    all_attributes = set(dir(obj)) 

    # --- Magic methods ---
    obj_map["magic_methods"] = classify_members(
        obj,
        all_attributes,
        lambda name, _: name.startswith("__") and name.endswith("__"),
    )

    # --- Internal methods ---
    obj_map["methods_internal"] = classify_members(
        obj,
        all_attributes,
        lambda name, val: callable(val) and (name.startswith("_") or name.endswith("_")),
    )

    # --- External methods ---
    obj_map["methods_external"] = classify_members(
        obj,
        all_attributes,
        lambda name, val: callable(val) and not (name.startswith("_") or name.endswith("_")),
    )

    # --- Properties ---
    for name, val in sorted(inspect.getmembers(obj.__class__)):
        if isinstance(val, property):
            obj_map["properties"][name] = val
            all_attributes.discard(name)

    # --- Internal attributes ---
    obj_map["attributes_internal"] = classify_members(
        obj,
        all_attributes,
        lambda name, _: name.startswith("_") or name.endswith("_"),
    )

    # --- External attributes ---
    obj_map["attributes_external"] = classify_members(
        obj,
        all_attributes,
        lambda name, val: not (name.startswith("_") or name.endswith("_")),
    )

    # --- Remaining unclassified ---
    for name in sorted(all_attributes):
        obj_map["others"][name] = safe_getattr(obj, name)
        all_attributes.discard(name)

    return obj_map

def inspect_object(
    obj: Any,
    categories: Optional[list[str]] = None,
    skip_empty: bool = False
) -> None:
    """
    Pretty-print an object map created by `map_object` using Rich.

    Args:
        obj (Any): The object to analyze and display.
        categories (list[str] | None): Which top-level categories of obj_map
            to display. Defaults to all categories.
        skip_empty (bool): If True, skip categories/elements that are empty.
    """
    obj_map = map_object(obj)
    console = Console()
    tree = Tree(
        f"[bold yellow]{obj_map['type_info']['type']} at <{obj_map['type_info']['id']}>[/bold yellow]"
    )

    def add_branch(parent: Tree, data: Any, label: str, depth: int = 0) -> None:
        """Recursive helper to add branches to the Rich tree."""
        if skip_empty and (data == {} or data == [] or data == () or data == set() or data is None):
            return

        if isinstance(data, dict) and depth < 1:
            branch = parent.add(f"[bold]{label}[/bold]")
            for key in sorted(data.keys()):
                add_branch(branch, data[key], str(key), depth + 1)
        else:
            parent.add(f"{label}: [green]{repr(data)}[/green]")

    # Choose categories
    selected_categories = categories or list(obj_map.keys())

    for key in sorted(selected_categories):
        if key not in obj_map:
            continue
        if skip_empty and not obj_map[key]:
            continue
        add_branch(tree, obj_map[key], str(key))

    console.print(tree)