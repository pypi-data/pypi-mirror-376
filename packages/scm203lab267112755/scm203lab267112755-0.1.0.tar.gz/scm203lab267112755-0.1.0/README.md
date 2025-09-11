# mypackage

`scm203lab267112755` is a lightweight Python package that provides numerical methods
for solving **roots of equations** and **initial value problems (ODEs)**.
It is designed mainly for learning purposes and as an example of Python packaging.

---

## Features
- **lab2mod167112755.py**: Secant method, False Position method  
- **lab2mod267112755.py**: 2nd-order Runge-Kutta (Heun), 3rd-order Runge-Kutta  

---

## Installation

You can install the package directly from PyPI:

---
### Example
if __name__ == "__main__":
    f = lambda x: ...
    root_secant = secant(f, x0, x1)
    print(f"\nRoot (Secant): {root_secant:.6f}")
    root_false_pos = false_position(f, a, b)
    print(f"\nRoot (False Position): {root_false_pos:.6f}")

if __name__ == "__main__":
    f = lambda t, y:...
    # Runge-Kutta 2nd order
    runge_kutta2(f, t0, y0, h, n)
    # Runge-Kutta 3rd order
    runge_kutta3(f, t0, y0, h, n)
```bash
pip install scm203lab267112755
