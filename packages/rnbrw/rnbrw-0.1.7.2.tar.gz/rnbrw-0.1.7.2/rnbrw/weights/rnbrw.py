import numpy as np
import random
from joblib import Parallel, delayed
from rnbrw.utils import normalize_edge_weights
import networkx as nx
from scipy.sparse import csr_matrix

def weights_to_edge_dict(weights, edge_list):
    return {tuple(edge_list[eid]): w for eid, w in weights.items()}

def graph_to_csr(G):
    """
    Convert a NetworkX undirected graph to CSR adjacency and an edge lookup.
    Ensures both (u,v) and (v,u) map to the SAME edge_id.

    Parameters
    ----------
    G : networkx.Graph
        Input graph (must be undirected)

    Returns
    -------
    indptr : np.ndarray
        CSR row pointer array
    indices : np.ndarray
        CSR column indices array
    edge_lookup : dict
        Mapping (u,v) -> edge_id (for both orientations)
    edge_list : np.ndarray
        Edge list of shape (m, 2), each undirected edge once
    n : int
        Number of nodes
    m : int
        Number of edges
    """
    # Relabel nodes to contiguous integers [0..n-1]
    mapping = {node: i for i, node in enumerate(G.nodes())}
    G = nx.relabel_nodes(G, mapping)

    n = G.number_of_nodes()
    m = G.number_of_edges()

    # CSR adjacency
    A = nx.to_scipy_sparse_array(G, format="csr", dtype=np.int32)

    # Build edge_lookup and edge_list
    edge_lookup = {}
    edge_list = []
    eid = 0
    for u, v in G.edges():
        edge_list.append((u, v))
        edge_lookup[(u, v)] = eid
        edge_lookup[(v, u)] = eid  # both orientations → same ID
        eid += 1

    edge_list = np.array(edge_list, dtype=np.int32)

    return A.indptr, A.indices, edge_lookup, edge_list, n, m

# ---------------------------------------------------------------------
def validate_csr_mapping(edge_lookup, edge_list, m):
    """
    Sanity check for CSR edge mapping consistency.

    Parameters
    ----------
    edge_lookup : dict
        Mapping (u,v) -> edge_id (both orientations must map to same ID)
    edge_list : np.ndarray
        Array of shape (m, 2), one undirected edge per row
    m : int
        Number of edges in the graph

    Raises
    ------
    AssertionError if any inconsistency is found.
    """
    # 1. Ensure edge_list has exactly m rows
    assert len(edge_list) == m, f"edge_list length {len(edge_list)} != m {m}"

    # 2. Ensure edge_lookup maps exactly 2m keys to m unique IDs
    ids = list(edge_lookup.values())
    assert len(ids) == 2*m, f"edge_lookup should have 2m entries, got {len(ids)}"
    assert len(set(ids)) == m, f"edge_lookup maps to {len(set(ids))} unique IDs, expected {m}"

    # 3. Ensure both orientations are present and map to the same ID
    for u, v in edge_list:
        id1 = edge_lookup.get((u, v))
        id2 = edge_lookup.get((v, u))
        assert id1 is not None and id2 is not None, f"Missing orientation for edge {(u,v)}"
        assert id1 == id2, f"Mismatch: (u,v) -> {id1}, (v,u) -> {id2}"

    print(" CSR edge mapping validated: consistent with RNBRW assumptions.")

# Core RNBRW primitives
# ---------------------------------------------------------------------

def walk_hole_E(G, S=None, seed=None):
    """
    RNBRW primitive.
    Defaults to S=m. In compute_weights(mode="E"), we call with S=2m
    to reproduce the paper-faithful 2m walkers setup.
    """
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)
    if S is None:
        S = G.number_of_edges()  # Default to m
    m = G.number_of_edges()
    edges = list(G.edges())
    T = np.zeros(m, dtype=int)

    # S = m (edges), sample with replacement
    sampled_edges = [edges[i] for i in np.random.choice(m, S, replace=True)]

    for x, y in sampled_edges:
        for u, v in [(x, y), (y, x)]:
            walk = [u, v]
            while True:
                nexts = list(G.neighbors(v))
                if u in nexts:
                    nexts.remove(u)

                if not nexts:
                    break

                nxt = random.choice(nexts)
                if nxt in walk:
                    T[G[v][nxt]['enum']] += 1
                    break

                walk.append(nxt)
                u, v = v, nxt
    return T

def walk_hole_E_csr(indptr, indices, edge_lookup, edge_list, m, S=None, seed=None):
    """
    Paper-faithful RNBRW primitive (2m runs), CSR backend.
    Each sampled edge is traversed in both directions (u->v and v->u).
    """
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)
    if S is None:
        S = m  # Default to m if not provided
    T = np.zeros(m, dtype=int)

    # Sample undirected edges uniformly with replacement
    #edge_list = [(u, v) for (u, v) in edge_lookup.keys() if u < v]
    L = np.random.choice(len(edge_list), S, replace=True)
    E_sampled = [edge_list[i] for i in L]

    for x, y in E_sampled:
        for u, v in [(x, y), (y, x)]:   # <-- both orientations
            walk = [u, v]
            while True:
                nbrs = indices[indptr[v]:indptr[v+1]]
                # remove backtrack
                nbrs = nbrs[nbrs != u]

                if len(nbrs) == 0:
                    break

                nxt = random.choice(nbrs)
                if nxt in walk:
                    e_id = edge_lookup.get((v, nxt))
                    if e_id is not None:
                        T[e_id] += 1
                    break

                walk.append(nxt)
                u, v = v, nxt
    return T


def walk_hole(G, S=None, seed=None):
    """
    HPC-friendly RNBRW primitive (configurable number of runs).
    Default S = floor(m/100), i.e. 1% of edges.
    """
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)

    m = G.number_of_edges()
    if S is None:
        S = max(1, int(np.floor(m / 100)))

    T = np.zeros(m, dtype=int)
    edges = list(G.edges())

    sampled_edges = [edges[i] for i in np.random.choice(m, S, replace=True)]

    for x, y in sampled_edges:
        for u, v in [(x, y), (y, x)]:
            walk = [u, v]
            while True:
                nexts = list(G.neighbors(v))
                if u in nexts:
                    nexts.remove(u)

                if not nexts:
                    break

                nxt = random.choice(nexts)
                if nxt in walk:
                    T[G[v][nxt]['enum']] += 1
                    break

                walk.append(nxt)
                u, v = v, nxt
    return T

def walk_hole_csr(indptr, indices, edge_lookup, edge_list, m, S=None, seed=None):
    """
    HPC-friendly RNBRW primitive (CSR backend).
    Each sampled edge is traversed in both directions (u->v and v->u).

    Parameters
    ----------
    indptr, indices : np.ndarray
        CSR adjacency representation of the graph
    edge_lookup : dict
        Mapping (u,v) -> edge_id
    m : int
        Number of edges
    S : int or None
        Number of sampled edges (default = floor(m/100), i.e. 1% of edges)
    seed : int or None
        Random seed for reproducibility

    Returns
    -------
    T : np.ndarray
        Retrace counts per edge (length m)
    """
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)

    if S is None:
        S = max(1, int(np.floor(m / 100)))  # 1% default

    T = np.zeros(m, dtype=int)
    #edge_list = [(u, v) for (u, v) in edge_lookup.keys() if u < v]

    L = np.random.choice(len(edge_list), S, replace=True)
    E_sampled = [edge_list[i] for i in L]

    for x, y in E_sampled:
        for u, v in [(x, y), (y, x)]:   # <-- both orientations
            walk = [u, v]
            while True:
                nbrs = indices[indptr[v]:indptr[v+1]]  # Get neighbors of v (CSR slice)
                nbrs = nbrs[nbrs != u]  # remove backtrack

                if len(nbrs) == 0:
                    break

                nxt = random.choice(nbrs)
                if nxt in walk:
                    e_id = edge_lookup.get((v, nxt))
                    if e_id is not None:
                        T[e_id] += 1
                    break

                walk.append(nxt)
                u, v = v, nxt
    return T

# ---------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------
def compute_weights(
    G=None,
    indptr=None,
    indices=None,
    edge_lookup=None,
    edge_list=None,
    m=None,
    nsim=None,
    seed=None,
    factor=1.0,
    n_jobs=1,
    init_weight=0.0001,
    mode="E",       # "E" = paper-faithful (2m runs), "sample" = scalable
    backend="nx",    # "nx" (NetworkX) or "csr" (sparse CSR)
    validate=False  # NEW: whether to run CSR mapping validation
):
    """
    Compute RNBRW edge weights.

    Parameters
    ----------
    G : networkx.Graph, optional
        Input graph (required if backend="nx").
    indptr, indices, edge_lookup, m : optional
        CSR representation (required if backend="csr").
    nsim : int or None
        Number of RNBRW runs (only used in mode="sample").
    seed : int or None
        Random seed for reproducibility.
    factor : float
        Scale factor for nsim when not provided.
    n_jobs : int
        Parallel jobs (-1 = all CPUs).
    init_weight : float
        Initial placeholder weight for edges.
    mode : str
        "E" = paper-faithful (2m runs).
        "sample" = HPC mode (default m/100 walkers).
    backend : str
        "nx" (NetworkX) or "csr" (sparse adjacency).

    Returns
    -------
    dict
        Edge weights as {edge_id: weight} (CSR backend).
    networkx.Graph
        Graph with 'ret' and 'ret_n' (NetworkX backend).
    """
    # -------------------------
    # NetworkX backend
    # -------------------------
    if backend == "nx":
        m = G.number_of_edges()

        # Initialize edge attributes
        for i, (u, v) in enumerate(G.edges()):
            G[u][v]['enum'] = i
            G[u][v]['ret'] = init_weight
            G[u][v]['ret_n'] = init_weight

        if mode == "E":
            # Paper-faithful: 2m runs
            T = walk_hole_E(G, seed=seed, S=2*m)

        elif mode == "sample":
            if nsim is None:
                nsim = int(m * factor)
            seeds = [(seed + i) if seed is not None else None for i in range(nsim)]
            results = Parallel(n_jobs=n_jobs)(
                delayed(walk_hole)(G, S=1, seed=s) for s in seeds
            )
            T = sum(results)

        else:
            raise ValueError("mode must be 'E' or 'sample'")

        # Normalize
        total = T.sum() if T.sum() > 0 else 1
        for i, (u, v) in enumerate(G.edges()):
            G[u][v]['ret'] = T[i]
            G[u][v]['ret_n'] = T[i] / total
        return G

    # -------------------------
    # CSR backend
    # -------------------------
    elif backend == "csr":
        # If CSR data is missing but G is provided → auto-convert
        if (indptr is None or indices is None or edge_lookup is None or edge_list is None or m is None):
            if G is None:
                raise ValueError("CSR backend requires either CSR inputs or a NetworkX graph (G).")
            indptr, indices, edge_lookup, edge_list, n, m = graph_to_csr(G)
        if validate:    
            validate_csr_mapping(edge_lookup, edge_list, m)  # Run validation once before walkers
        
        if mode == "E":
            # Paper-faithful: 2m runs
            T = walk_hole_E_csr(indptr, indices, edge_lookup, edge_list, m, seed=seed, S=2*m)

        elif mode == "sample":
            if nsim is None:
                nsim = int(m * factor)
            seeds = [(seed + i) if seed is not None else None for i in range(nsim)]
            results = Parallel(n_jobs=n_jobs)(
                delayed(walk_hole_csr)(indptr, indices, edge_lookup, edge_list, m,
                                       S=1, seed=s)
                for s in seeds
            )
            T = sum(results)

        else:
            raise ValueError("mode must be 'E' or 'sample'")

        # Normalize
        total = T.sum() if T.sum() > 0 else 1
        weights = {eid: T[eid] / total for eid in range(m)}
        return weights