from .rnbrw import (
    compute_weights,
    graph_to_csr,
    validate_csr_mapping,
    walk_hole,
    walk_hole_csr,
    walk_hole_E,
    walk_hole_E_csr,
    weights_to_edge_dict,   # <-- add this
)

__all__ = [
    "compute_weights",
    "graph_to_csr",
    "validate_csr_mapping",
    "walk_hole",
    "walk_hole_csr",
    "walk_hole_E",
    "walk_hole_E_csr",
    "weights_to_edge_dict",  # <-- and this
]
