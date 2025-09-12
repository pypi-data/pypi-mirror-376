from copy import copy
from typing import Hashable

PYMAX = max
PYMIN = min
PYABS = abs

def envelope_tree(
        tree: dict | list, 
        levels: list[Hashable | None], 
        leaf: Hashable | None, 
        agg_func: callable, 
        with_trace: bool = True
    ) -> dict:
    """
    Returns a new dict tree
    """
    env_acc = {}
    # If we are at the last branch...
    if not levels:
        if isinstance(tree, list):
            orig_tree = tree
            tree = {idx: value for idx, value in enumerate(tree)}
        elif isinstance(tree, dict):
            orig_tree = tree
            tree = {idx: branch[leaf] for idx, branch in enumerate(tree.values())}
            trace_tree = {idx: key for idx, key in enumerate(orig_tree.keys())}

        # leaf_acc = {}
        # for leaf_key, leaf_value in tree.items():
        #     if leaf is not None and leaf_key == leaf:
        #         leaf_acc.update({leaf_key: leaf_value})
        #     else:
        #         leaf_acc = tree

        # ...create a dict of the enveloped value and the key
        # that it belongs to and return it.
        # env_values = list(leaf_acc.values())
        env_values = list(tree.values())
        env_value = agg_func(env_values)
        # env_keys = list(leaf_acc.keys())
        try:
            env_key = trace_tree[env_values.index(env_value)]
        except ValueError: # The value was transformed, likely due to abs()
            env_key = trace_tree[env_values.index(-1 * env_value)]
        env_acc.update({"key": env_key, "value": env_value})
        if with_trace:
            return env_acc
        else:
            return env_value
    else:
        # Otherwise, pop the next level and dive into the tree on that branch
        level = levels[0]
        if level is not None:
            try:
                tree[level]
            except KeyError:
                raise KeyError(
                    f"Key '{level}' does not exist at this level. Available keys: {list(tree.keys())}. "
                    "Perhaps not all of your tree elements have the same keys. Try enveloping over trees "
                    "that have the same branch structure and leaf names."               
                )
            env_acc.update({level: envelope_tree(tree[level], levels[1:], leaf, agg_func, with_trace)})
            return env_acc
        else:
            # If None, then walk all branches of this node of the tree
            if isinstance(tree, list):
                tree = {idx: leaf for idx, leaf in enumerate(tree)}
            for k, v in tree.items():
                env_acc.update({k: envelope_tree(v, levels[1:], leaf, agg_func, with_trace)})
            return env_acc

    
def absmax(x: list[float | int]) -> float | int:
    """
    Returns the absolute maximum value in 'x'.
    """
    abs_acc = [abs(y) for y in x]
    return max(abs_acc)


def absmin(x: list[float | int]) -> float | int:
    """
    Returns the absolute minimum value in 'x'.
    """
    abs_acc = [abs(y) for y in x]
    return min(abs_acc)


def max(x: list[float | int | None]) -> float | int | None:
    """
    Returns the max value in 'x' while ignoring "None".
    If all values in 'x' are None, then None is returned.
    """
    return PYMAX([y for y in x if y is not None])


def min(x: list[float | int | None]) -> float | int | None:
    """
    Returns the max value in 'x' while ignoring "None".
    If all values in 'x' are None, then None is returned.
    """
    return PYMIN([y for y in x if y is not None])


def abs(x: float | int | None) -> float | int | None:
    """
    Performs abs but passes None through if x is None.
    """
    if x is None:
        return x
    return PYABS(x)