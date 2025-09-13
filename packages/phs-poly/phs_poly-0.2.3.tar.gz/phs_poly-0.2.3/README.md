# phs_poly

Procedures for generating **RBF-FD weights** for derivative calculations.  
Currently only **PHS + poly** approximations in 2-d are supported.

---

## Installation

To install use,

```
pip install phs_poly
```

Requirements_
- A Fortran compiler (e.g. `gfortran` or `flang`)
- A LAPACK library (e.g. OpenBLAS, Accelerate, ArmPL)
- NumPy

## Quickstart

```python
import phs_poly

# ... set x- and y-coordinates, initialize work and coeff arrays ...

ierr = phs_poly.phs3_poly2(n,x,y,coeffs,ldc,wrk,iwrk)

# First derivatives weights
wx = coeffs[0:n,0] 
wy = coeffs[0:n,1]

# Second derivative weights
wxx = coeffs[0:n,2] 
wxy = coeffs[0:n,3]
wyy = coeffs[0:n,4]
```

## Features

* RBF-FD weights for derivative operators
* PHS + poly based approximation
* Designed for 2-d problems

![Approximation of scattered function](./taylor_mesh.png)
‚ 
## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.
