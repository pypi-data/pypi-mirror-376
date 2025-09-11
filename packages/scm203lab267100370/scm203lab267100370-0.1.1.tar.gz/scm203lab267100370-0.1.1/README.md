# Package name : scm203lab267100370

`adisak_utils` is a lightweight Python package that provides simple utility functions
for **Roots of Equation in One Variable**, and **Initial Value Problems for a first-order differential equation**.
It is designed mainly for learning purposes and as an example of Python packaging.

---

## Features
- **Roots of Equation in One Variable**: Solve f(x)=0, where funtion is a continuous function. Methods include : Bisection Method and Fixed-Point Iteration

- **Initial Value Problems for a first-order differential equation**:Solve a differential equation. Methods include : Euler’s Method and 4-order Runge-Kutta method.
---

## Installation

You can install the package directly from PyPI:'

```bash
pip install adisak_utils
```
---

## Example
- **Roots of Equation in One Variable**
```
    f = lambda x: x**3 - x - 2
    g = lambda x: (x + 2)**(1/3)
    
    a, b = 1, 2
    x0 = 1.5
    nMax = 10
    TOL = 0.0001

    print("Bisection Method:")
    bisection_data = bisection(f, a, b, nMax, TOL)

    print("Fixed Point Iteration Method:")
    fixpoint_data = fixpoint(g, x0, nMax, TOL)
```


- **Initial Value Problems for a first-order differential equation**
```
    f = lambda x,y: x + y
    x0, y0 = 0, 1
    xStop = 0.4
    h = 0.1
    n = int((xStop - x0) / h)
    
    print("Euler's Method:")
    euler_method(f, x0, y0, xStop, h)
    
    print("Runge-Kutta 4th Order Method:")
    kut4(f, x0, y0, xStop, h)
```
