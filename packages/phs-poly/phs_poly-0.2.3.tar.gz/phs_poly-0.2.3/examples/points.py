import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import qmc

from scipy.spatial import KDTree
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import reverse_cuthill_mckee

from math import sqrt

import phs_poly
import time
import warnings

# --- Parameters ------------------------------------------
radius = 0.01         # minimal Poisson-disk radius
seed = 42
n_interior = 10000      # requested number of interior samples (PoissonDisk may return fewer)
n_edge = 20           # samples per edge

# --- Produce interior Poisson-disk points ----------------
rng = np.random.default_rng(seed)
engine = qmc.PoissonDisk(d=2, radius=radius)
interior = engine.random(n_interior)  # you can also try engine.fill_space()

# --- set these to your domain sizes ---
Lx, Ly = 1.0, 1.0
box = np.array([Lx, Ly])

# ensure points are inside the fundamental cell (cKDTree demands this)
interior = interior % box

# build periodic tree
tree = KDTree(interior, boxsize=box)

N = interior.shape[0]
ss = 20

data = np.empty(N*ss, dtype=np.float64)
indices = np.empty(N*ss, dtype=np.int32)
indptr = np.empty(N+1, dtype=np.int32)
indptr[0] = 0

# your workspace / coeff arrays (unchanged)
np_ = ss + 10
ldc = np_
coeffs = np.zeros((ldc, 5),order='F')
wrk = np.zeros((ldc, np_),order='F')
iwrk = np.zeros(np_, dtype=np.int32)

# Advection velocity
cx, cy = 1.0, 1.0
dt = 0.0001

for k, node in enumerate(interior):

    # query k = ss nearest neighbors (includes self as nearest)
    dists, nbrs = tree.query(node, k=ss)
    nbrs = np.atleast_1d(nbrs).astype(np.int32)   # shape (ss,)

    # neighbor coordinates and displacements
    neigh = interior[nbrs]
    dx = neigh[:, 0] - node[0]
    dy = neigh[:, 1] - node[1]

    # minimum-image convention (always periodic)
    dx[dx <  -0.5 * Lx] += Lx
    dx[dx >=  0.5 * Lx] -= Lx
    dy[dy <  -0.5 * Ly] += Ly
    dy[dy >=  0.5 * Ly] -= Ly

    x, y = dx, dy

    # index bookkeeping
    iaa = indptr[k]
    iab = iaa + ss
    indptr[k+1] = iab
    indices[iaa:iab] = nbrs

    # call the Fortran routine with actual number of neighbors m
    m = nbrs.size
    ierr = phs_poly.phs3_poly3(m, x, y, coeffs, ldc, wrk, iwrk)
    if ierr != 0:
        raise RuntimeError(f"phs3_poly2 failed with ierr={ierr}")

    # Laplacian weights: sum coeffs[:,2] + coeffs[:,4]; pad if needed
    vals = np.zeros(ss, dtype=np.float64)
#    vals[:m] = coeffs[:m, 2] + coeffs[:m, 4]

    # Lax-Wendroff operator
    vals[:m] = -dt*(cx*coeffs[:m,0] + cy*coeffs[:m,1]) \
        + 0.5*dt**2*(cx*cx*coeffs[:m, 2] + 2*cx*cy*coeffs[:m, 3] + cy*cy*coeffs[:m,4])

    data[iaa:iab] = vals

spmat = csr_matrix((data, indices, indptr), shape=(N, N))

# compute permutation vector
perm = reverse_cuthill_mckee(spmat)

start = time.perf_counter()

# apply permutation: A_perm = P * A * P^T
A_perm = spmat[perm, :][:, perm]
#A_perm = spmat[perm, perm.T]

end = time.perf_counter()
print(f"A: Elapsed time: {end - start:.6f} seconds")

#interior = interior[perm,:]

# Gaussian parameters
center = np.array([0.5, 0.5])
sigma = 0.1  # adjust width as needed

# Evaluate Gaussian at each interior point
diff = interior - center
gaussian_values = np.exp(-np.sum(diff**2, axis=1) / (2*sigma**2))

y0 = gaussian_values.copy()
y = gaussian_values.copy()
nsteps = int(sqrt(2.0)/(dt*sqrt(cx**2 + cy**2)))
print(f"nsteps = {nsteps}")

start = time.perf_counter()
for step in range(nsteps):
    y += spmat @ y
end = time.perf_counter()
elapsed_per_step = (end - start)/nsteps
print(f"A: time per matvec : {elapsed_per_step:.6f} seconds")

nbytes = spmat.nnz*(8 + 4) + y.size*(8 + 8) + y.size*(8*8)
effective_bw = nbytes / elapsed_per_step * 1.0e-9

print(f"A: effective_bw : {effective_bw} GB/s")


#A_perm = spmat.copy()
#A_perm.indices = perm.take(A_perm.indices)


# ---------------- Plot ----------------
plt.figure(figsize=(7, 7))
plt.scatter(interior[:, 0], interior[:, 1], c=y, s=20,
    alpha=0.6, label="initial interior")
#plt.scatter(interior_annealed[:, 0], interior_annealed[:, 1], s=20, alpha=0.9, color="C1", label="annealed interior")
#plt.scatter(edges[:, 0], edges[:, 1], s=30, color="k", marker="x", label="fixed edges")
plt.legend()
plt.gca().set_aspect("equal")
plt.xlim(-0.02, 1.02)
plt.ylim(-0.02, 1.02)
plt.title("Poisson-disk interior (annealed) + fixed boundary nodes")
plt.show()

# plot side by side
fig, axes = plt.subplots(1, 2, figsize=(12, 6))

axes[0].spy(spmat, markersize=1)
axes[0].set_title("Original")

axes[1].spy(A_perm, markersize=1)
axes[1].set_title("RCM Permuted")

plt.tight_layout()
plt.show()

