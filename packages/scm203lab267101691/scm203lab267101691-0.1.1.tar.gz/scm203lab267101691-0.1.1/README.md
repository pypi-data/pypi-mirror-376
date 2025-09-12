`scm203lab267101691` is a lightweight Python package that provides simple utility functions
for **The bisection method**, **Newton's method**, **3-order Runge-Kutta method** and **4-order Runge-Kutta method**.
It is designed mainly for learning purposes and as an example of Python packaging.

---

## Features
- **Module 1**
    - **The bisection method**: finding root of f in [a,b] with error tolerance
    - **Newton's method**: finding root of f with initial guess x0 and error tolerance
- **Module 2**
    - **3-order Runge-Kutta method**: solve the ODE y' = f(t, y) using the 3rd-order Runge-Kutta method.
    - **4-order Runge-Kutta method**: solve the ODE y' = f(t, y) using the 4th-order Runge-Kutta method.

---

## Installation

You can install the package directly from PyPI:

```bash
pip install scm203lab267101691
```

## Examples
```bash
import scm203lab267101691 as scm
print("bisection ≈",scm.bisection(lambda x: x**3+x-1,0,1,0.001,10))
print("newton ≈",scm.newton(lambda x: x**3+x-1,lambda x: 3*x**2+1,1,0.001,10))
print(scm.order_3_runge(lambda t, y: y - t**2 + 1, 0, 2, 10, 0.5))
print(scm.order_4_runge(lambda t, y: y - t**2 + 1, 0, 2, 10, 0.5))
```