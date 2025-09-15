"""
Lift-the-Weakest adaptive subset selection and weighted-average RDM estimation.

Implements:
- Evidence-weighted, iteratively scaled RDM estimation from multiple subset arrangements
- Lift-the-weakest next-trial subset selection maximizing estimated trial efficiency
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Iterable
import math
import numpy as np


@dataclass
class TrialArrangement:
    """A single trial's arrangement outcome.

    Attributes:
        subset: list of global item indices included in the trial
        positions: mapping from item index to (x, y) in on-screen coordinates
    """
    subset: List[int]
    positions: Dict[int, Tuple[float, float]]


def _pairwise_distances_from_positions(indices: List[int], positions: Dict[int, Tuple[float, float]]) -> np.ndarray:
    """Compute an (m x m) Euclidean distance matrix for given indices from positions.

    Returns distances in on-screen units (unscaled as placed by the subject).
    """
    m = len(indices)
    D = np.zeros((m, m), dtype=float)
    for i in range(m):
        xi, yi = positions[indices[i]]
        for j in range(i + 1, m):
            xj, yj = positions[indices[j]]
            d = math.hypot(xi - xj, yi - yj)
            D[i, j] = D[j, i] = d
    return D


def _rms(values: np.ndarray) -> float:
    vals = values.astype(float)
    return float(np.sqrt(np.mean(vals * vals))) if values.size else 0.0


def _scale_to_match_rms(A: np.ndarray, B: np.ndarray) -> float:
    """Return scale factor s to make RMS(s*A) match RMS(B). If A has zero RMS, return 1.0.
    Only upper triangle (excluding diagonal) contributes.
    """
    # Use off-diagonal entries
    iu = np.triu_indices_from(A, k=1)
    rms_A = _rms(A[iu])
    rms_B = _rms(B[iu])
    if rms_A <= 1e-12:
        # If A has ~no energy, scaling is undefined; return 0 to keep it at zero
        return 0.0
    return rms_B / rms_A


def estimate_rdm_weighted_average(
    n_items: int,
    trials: Iterable[TrialArrangement],
    *,
    max_iter: int = 30,
    tol: float = 1e-6,
) -> Tuple[np.ndarray, np.ndarray]:
    """Estimate full RDM (n x n) via weighted average of iteratively scaled subset RDMS.

    Weight per pair in a trial is the square of the unscaled on-screen distance (evidence weight).
    Each trial subset distance matrix is scaled to match the current RDM estimate on its pairs.

    Args:
        n_items: total item count
        trials: iterable of TrialArrangement
        max_iter: maximum iterations for alternating scaling/averaging
        tol: RMS difference threshold for convergence

    Returns:
        (D_est, W)
        - D_est: estimated full dissimilarity matrix (n x n), symmetric, zeros on diagonal
        - W: accumulated evidence weights matrix (n x n), symmetric, zeros on diagonal
    """
    trials = list(trials)
    # Precompute per-trial subset index mapping and distance matrices
    trial_info = []
    for t in trials:
        subset = list(t.subset)
        m = len(subset)
        if m < 2:
            continue
        D_sub = _pairwise_distances_from_positions(subset, t.positions)
        trial_info.append((subset, D_sub))

    # Initialize W with normalized evidence weights per trial: (d_ij / max_d)^2
    W = np.zeros((n_items, n_items), dtype=float)
    for subset, D_sub in trial_info:
        m = len(subset)
        iu_sub = np.triu_indices(m, 1)
        maxd = float(np.max(D_sub[iu_sub])) if iu_sub[0].size else 0.0
        scale = (1.0 / maxd) if maxd > 1e-12 else 0.0
        for a in range(m):
            ia = subset[a]
            for b in range(a + 1, m):
                ib = subset[b]
                dij = D_sub[a, b] * scale
                w = dij * dij
                W[ia, ib] += w
                W[ib, ia] += w

    # Seed current estimate D
    D = np.zeros((n_items, n_items), dtype=float)
    # If any full arrangement present, use it as seed (scaled to RMS=1)
    seed_found = False
    for subset, D_sub in trial_info:
        if len(subset) == n_items:
            # Directly set full D from this arrangement
            D[:, :] = 0.0
            for a in range(n_items):
                for b in range(a + 1, n_items):
                    D[a, b] = D[b, a] = D_sub[a, b]
            seed_found = True
            break

    if not seed_found:
        # Use evidence-weighted average of unscaled distances, embedded into full matrix
        num = np.zeros((n_items, n_items), dtype=float)
        den = np.zeros((n_items, n_items), dtype=float)
        for subset, D_sub in trial_info:
            m = len(subset)
            for a in range(m):
                ia = subset[a]
                for b in range(a + 1, m):
                    ib = subset[b]
                    w = D_sub[a, b] ** 2
                    num[ia, ib] += D_sub[a, b] * w
                    den[ia, ib] += w
                    num[ib, ia] += D_sub[a, b] * w
                    den[ib, ia] += w
        with np.errstate(invalid="ignore", divide="ignore"):
            D = np.divide(num, den, out=np.zeros_like(num), where=den > 0)
            D = np.nan_to_num(D)

    # Scale D to RMS 1 (off-diagonal)
    iu = np.triu_indices(n_items, 1)
    rms_D = _rms(D[iu])
    if rms_D > 0:
        D *= (1.0 / rms_D)

    # Alternating scaling / averaging
    for _ in range(max_iter):
        D_prev = D.copy()

        # For each trial, compute scale to match D on its pairs
        scaled_subs: List[Tuple[List[int], np.ndarray, np.ndarray]] = []
        for subset, D_sub in trial_info:
            # Extract current D on subset
            m = len(subset)
            D_slice = np.zeros((m, m), dtype=float)
            for a in range(m):
                ia = subset[a]
                for b in range(m):
                    ib = subset[b]
                    D_slice[a, b] = D[ia, ib]
            s = _scale_to_match_rms(D_sub, D_slice)
            scaled = D_sub * s
            scaled_subs.append((subset, scaled, D_sub))  # keep unscaled for weights

        # Weighted average across trials
        num = np.zeros((n_items, n_items), dtype=float)
        den = np.zeros((n_items, n_items), dtype=float)
        for subset, D_scaled, D_unscaled in scaled_subs:
            m = len(subset)
            iu_sub = np.triu_indices(m, 1)
            maxd = float(np.max(D_unscaled[iu_sub])) if iu_sub[0].size else 0.0
            scale_w = (1.0 / maxd) if maxd > 1e-12 else 0.0
            for a in range(m):
                ia = subset[a]
                for b in range(a + 1, m):
                    ib = subset[b]
                    # evidence weight normalized within each trial
                    dij = D_unscaled[a, b] * scale_w
                    w = dij * dij
                    num[ia, ib] += D_scaled[a, b] * w
                    den[ia, ib] += w
                    num[ib, ia] += D_scaled[a, b] * w
                    den[ib, ia] += w
        with np.errstate(invalid="ignore", divide="ignore"):
            D = np.divide(num, den, out=np.zeros_like(num), where=den > 0)
            D = np.nan_to_num(D)

        # Scale to RMS 1 (off-diagonal)
        rms_D = _rms(D[iu])
        if rms_D > 0:
            D *= (1.0 / rms_D)

        # Convergence
        diff = _rms((D - D_prev)[iu])
        if diff < tol:
            break

    np.fill_diagonal(D, 0.0)
    np.fill_diagonal(W, 0.0)
    return D, W


def _utility(w: float, d: float) -> float:
    return 1.0 - math.exp(-w * d)


def _total_utility(W: np.ndarray, d: float) -> float:
    iu = np.triu_indices_from(W, k=1)
    return float(np.sum(1.0 - np.exp(-W[iu] * d)))


def _predict_evidence_gain_for_subset(
    subset: List[int],
    D: np.ndarray,
    *,
    arena_max: float = 1.0,
) -> Dict[Tuple[int, int], float]:
    """Estimate added evidence weights ΔW for a candidate subset.

    Scales D[subset] so that its maximum pair distance maps to `arena_max`.
    Evidence increment for pair (i,j) is predicted_on_screen_distance^2.
    """
    m = len(subset)
    if m < 2:
        return {}
    # Extract current dissimilarities
    D_sub = np.zeros((m, m), dtype=float)
    for a in range(m):
        ia = subset[a]
        for b in range(m):
            ib = subset[b]
            D_sub[a, b] = D[ia, ib]
    # Scale so max off-diagonal equals arena_max
    iu = np.triu_indices(m, 1)
    maxd = float(np.max(D_sub[iu])) if iu[0].size else 0.0
    s = (arena_max / maxd) if maxd > 1e-12 else 1.0
    D_pred = D_sub * s

    dW: Dict[Tuple[int, int], float] = {}
    for a in range(m):
        ia = subset[a]
        for b in range(a + 1, m):
            ib = subset[b]
            d_ij = D_pred[a, b]
            dW[(min(ia, ib), max(ia, ib))] = d_ij * d_ij
    return dW


def _trial_cost(n_items: int, exponent: float = 1.5) -> float:
    return n_items ** exponent


def select_next_subset_lift_weakest(
    D: np.ndarray,
    W: np.ndarray,
    *,
    utility_exponent: float = 10.0,
    time_cost_exponent: float = 1.5,
    arena_max: float = 1.0,
    min_size: int = 3,
    max_size: Optional[int] = None,
) -> List[int]:
    """Greedy lift-the-weakest subset selection maximizing trial efficiency.

    Starts from the globally weakest-evidence pair, adds items greedily that
    maximize (utility gain) / (time cost), and stops when no addition improves TE.
    """
    n = D.shape[0]
    # 1–2: weakest pair
    masked = W.copy()
    np.fill_diagonal(masked, np.inf)
    # Use upper triangle for argmin
    iu = np.triu_indices(n, 1)
    if iu[0].size == 0:
        return []
    flat_idx = np.argmin(masked[iu])
    j, k = iu[0][flat_idx], iu[1][flat_idx]

    nextISS: List[int] = [j, k]
    # Diagnostic
    print(f"[debug] Weakest-evidence pair start: ({j}, {k}), min W={masked[j,k]:.6f}")
    curTE = 0.0

    available = set(range(n))
    available.discard(j)
    available.discard(k)

    if max_size is None:
        max_size = n

    # Phase 1: grow to required minimum size regardless of TE sign
    while len(nextISS) < min_size and len(nextISS) < max_size and available:
        best_te = -1e18
        best_item: Optional[int] = None
        for i in list(available):
            candidate = nextISS + [i]
            dW = _predict_evidence_gain_for_subset(candidate, D, arena_max=arena_max)
            delta = 0.0
            for (a, b), inc in dW.items():
                w0 = W[a, b]
                delta += (_utility(w0 + inc, utility_exponent) - _utility(w0, utility_exponent))
            cost = _trial_cost(len(candidate), exponent=time_cost_exponent)
            te = (delta / cost) if cost > 0 else -1e18
            if te > best_te:
                best_te = te
                best_item = i
        if best_item is None:
            break
        nextISS.append(best_item)
        available.discard(best_item)
        curTE = best_te
        print(f"[debug] Grow-> added {best_item}, size={len(nextISS)}, TE={curTE:.6f}")

    # Phase 2: continue greedily only if TE improves
    while len(nextISS) < max_size and available:
        best_te = -1.0
        best_item: Optional[int] = None
        for i in list(available):
            candidate = nextISS + [i]
            # Predict evidence gain for this subset
            dW = _predict_evidence_gain_for_subset(candidate, D, arena_max=arena_max)
            # Compute utility gain only over affected pairs
            gain_pairs = list(dW.items())
            # Efficient utility delta: sum over only affected pairs
            delta = 0.0
            for (a, b), inc in gain_pairs:
                w0 = W[a, b]
                delta += (_utility(w0 + inc, utility_exponent) - _utility(w0, utility_exponent))
            # Cost
            cost = _trial_cost(len(candidate), exponent=time_cost_exponent)
            te = (delta / cost) if cost > 0 else 0.0
            if te > best_te:
                best_te = te
                best_item = i

        if best_item is None:
            break
        # Termination if no improvement
        if best_te <= curTE:
            print(f"[debug] Stop growth: best_te={best_te:.6f} <= curTE={curTE:.6f}")
            break
        # Otherwise, accept the item
        nextISS.append(best_item)
        available.discard(best_item)
        curTE = best_te
        print(f"[debug] Add-> {best_item}, size={len(nextISS)}, TE={curTE:.6f}")

    # Final guard: ensure minimum size if somehow not met
    if len(nextISS) < min_size and available:
        need = min_size - len(nextISS)
        for i in list(available)[:need]:
            nextISS.append(i)
            available.discard(i)
        print(f"[debug] Fallback to reach min_size: size={len(nextISS)}")

    return nextISS


def _classical_mds_2d(D: np.ndarray) -> np.ndarray:
    """Classical MDS to 2D embedding from a distance matrix D.

    Returns (n x 2) coordinates. If D is degenerate, returns zeros.
    """
    n = D.shape[0]
    if n == 0:
        return np.zeros((0, 2), dtype=float)

    # Double-centering: B = -0.5 * J D^2 J
    J = np.eye(n) - np.ones((n, n)) / n
    D2 = D ** 2
    B = -0.5 * J @ D2 @ J
    # Eigen-decomposition
    try:
        w, V = np.linalg.eigh(B)
    except np.linalg.LinAlgError:
        return np.zeros((n, 2), dtype=float)
    # Take top 2 components
    idx = np.argsort(w)[::-1]
    w = w[idx]
    V = V[:, idx]
    w = np.clip(w, 0, None)
    if w[0] <= 1e-12:
        return np.zeros((n, 2), dtype=float)
    L = np.diag(np.sqrt(w[:2])) if len(w) >= 2 else np.diag([math.sqrt(w[0]), 0.0])
    X = V[:, :2] @ L
    return X


def refine_rdm_inverse_mds(
    D_init: np.ndarray,
    trials: Iterable[TrialArrangement],
    *,
    max_iter: int = 20,
    tol: float = 1e-4,
    step_c: float = 0.3,
) -> np.ndarray:
    """Inverse MDS refinement: iteratively reduce arrangement prediction error.

    Args:
        D_init: initial full RDM estimate (n x n), symmetric with zeros diagonal
        trials: trial arrangements (subsets and on-screen positions)
        max_iter: maximum refinement iterations
        tol: RMS disparity threshold for stopping
        step_c: adjustment factor for dissimilarity update (c in the description)

    Returns:
        Refined RDM (n x n)
    """
    n = D_init.shape[0]
    D = D_init.copy().astype(float)
    np.fill_diagonal(D, 0.0)

    # Prepare trial subset true on-screen distance matrices
    trials = list(trials)
    trial_data: List[Tuple[List[int], np.ndarray]] = []
    for t in trials:
        subset = list(t.subset)
        if len(subset) < 2:
            continue
        D_obs = _pairwise_distances_from_positions(subset, t.positions)
        trial_data.append((subset, D_obs))

    iu_full = np.triu_indices(n, 1)

    for _ in range(max_iter):
        # Normalize D to RMS 1 off-diagonal
        rmsD = _rms(D[iu_full])
        if rmsD > 0:
            D *= (1.0 / rmsD)

        # Collect disparities per pair averaged across trials
        num_adj = np.zeros((n, n), dtype=float)
        cnt_adj = np.zeros((n, n), dtype=float)

        all_disparities: List[float] = []

        for subset, D_obs in trial_data:
            m = len(subset)
            # Predicted arrangement via MDS on current D subset
            D_sub = np.zeros((m, m), dtype=float)
            for a in range(m):
                ia = subset[a]
                for b in range(m):
                    ib = subset[b]
                    D_sub[a, b] = D[ia, ib]

            # Predict 2D embedding from D_sub using metric-stress MDS (SMACOF)
            X_pred = _smacof_mds_2d(D_sub)
            # Distances from predicted embedding
            D_pred = np.zeros((m, m), dtype=float)
            for a in range(m):
                for b in range(a + 1, m):
                    d = np.linalg.norm(X_pred[a] - X_pred[b])
                    D_pred[a, b] = D_pred[b, a] = d

            # Skip degenerate predictions (no variance)
            iu = np.triu_indices(m, 1)
            if iu[0].size == 0:
                continue
            if float(np.max(D_pred[iu])) <= 1e-12:
                # If prediction collapsed, skip this trial contribution
                continue

            # Scale predicted and observed to match RMS of their corresponding entries in D_sub
            s_pred = _scale_to_match_rms(D_pred, D_sub)
            s_obs = _scale_to_match_rms(D_obs, D_sub)
            D_pred_scaled = D_pred * s_pred
            D_obs_scaled = D_obs * s_obs

            # Disparities: predicted - observed (scaled)
            disp = D_pred_scaled - D_obs_scaled
            iu = np.triu_indices(m, 1)
            all_disparities.extend(disp[iu].ravel().tolist())

            # Accumulate per-pair adjustments in full space
            for a in range(m):
                ia = subset[a]
                for b in range(a + 1, m):
                    ib = subset[b]
                    num_adj[ia, ib] += disp[a, b]
                    num_adj[ib, ia] += disp[a, b]
                    cnt_adj[ia, ib] += 1.0
                    cnt_adj[ib, ia] += 1.0

        # Check RMS of disparities
        all_disparities = np.array(all_disparities, dtype=float)
        if all_disparities.size:
            rms_disp = _rms(all_disparities)
            if rms_disp < tol:
                break

        # Average adjustments
        with np.errstate(invalid="ignore", divide="ignore"):
            A = np.divide(num_adj, cnt_adj, out=np.zeros_like(num_adj), where=cnt_adj > 0)
            A = np.nan_to_num(A)
        # Update D
        D = D - step_c * A
        D[D < 0] = 0.0
        np.fill_diagonal(D, 0.0)

    # Final normalization
    rmsD = _rms(D[iu_full])
    if rmsD > 0:
        D *= (1.0 / rmsD)
    np.fill_diagonal(D, 0.0)
    return D


def _smacof_mds_2d(
    D: np.ndarray,
    *,
    max_iter: int = 200,
    eps: float = 1e-6,
    random_state: int = 0,
) -> np.ndarray:
    """Metric-stress MDS (SMACOF) to 2D for a dissimilarity matrix D.

    Weights are uniform (1 for i!=j). Returns (n x 2) coordinates.
    """
    n = D.shape[0]
    if n == 0:
        return np.zeros((0, 2), dtype=float)

    # Initial configuration: use classical MDS for a stable start
    X = _classical_mds_2d(D)
    if not np.any(X):
        rng = np.random.default_rng(random_state)
        X = rng.standard_normal((n, 2)) * 1e-3

    # Weights
    W = np.ones((n, n), dtype=float) - np.eye(n)
    V = np.diag(np.sum(W, axis=1))  # (n-1) on diagonal
    Vinv = np.linalg.pinv(V)

    def _pairwise_dist(X):
        # Euclidean distances
        diff = X[:, None, :] - X[None, :, :]
        return np.sqrt(np.sum(diff * diff, axis=2))

    def _stress(Dhat):
        # Stress-1: sum_{i<j} (d_ij - delta_ij)^2 with unit weights
        iu = np.triu_indices(n, 1)
        return float(np.sum((Dhat[iu] - D[iu]) ** 2))

    prev = np.inf
    for _ in range(max_iter):
        Dhat = _pairwise_dist(X)
        # Avoid division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = np.divide(D, Dhat, out=np.zeros_like(D), where=Dhat > 1e-12)
        B = -W * ratio
        np.fill_diagonal(B, 0.0)
        # Set diagonal: b_ii = - sum_{j != i} b_ij
        np.fill_diagonal(B, -np.sum(B, axis=1))

        # Update
        X_new = Vinv @ (B @ X)
        # Center to remove translation
        X_new -= np.mean(X_new, axis=0, keepdims=True)

        # Check convergence by stress
        Dhat_new = _pairwise_dist(X_new)
        cur = _stress(Dhat_new)
        if prev - cur <= eps * prev:
            X = X_new
            break
        X = X_new
        prev = cur

    return X
