# scm20367104703

`scm20367104703`is A example package to find Roots of eqaution and solves an ordinary differential equation (ODE).

---

## Features
- **Fixed-Point Iteration**: use a function `fixed_point()` to use Fixed_point method
- **Secant Method**: use a function `secant()` to use Secant method
- **2nd-order Runge-Kutta**: Use function `rk2()`solves an ordinary differential equation (ODE) of the form 
$$
\frac{dy}{dx} = f(t, y)
$$
using the 2nd-order Runge-Kutta method (Midpoint Method).
- **5nd-order Runge-Kutta** : Use `rk5()` Solves the same type of ODE using a more accurate 5th-order Runge-Kutta method.
---

## Installation

You can install the package directly from PyPI:

```
pip install scm20367104703

```
---

## Example1
```
    def g(x):
        return (x**2 + 3) / 5
    initial_guess = 0.5
    root, iterations = fixed_point(g, initial_guess)
    print(f"\nApproximate: {root}")
```
---
## Example2
```
    def f(x):
        return x**3 - x - 2
    root, iterations = secant(f, 1, 2)
    print(f"\nApproximate : {root}")

```
---
## Example3
```
    def f(t, y):
        return y - t**2 + 1
    t0 = 0.0
    y0 = 0.5
    h = 0.5
    n_steps = 8
    rk2(f, t0, y0, h, n_steps)
```
---
## Example4
```
    def f(t, y):
        return y - t**2 + 1
    t0 = 0.0
    y0 = 0.5
    h = 0.5
    n_steps = 8
    rk5(f, t0, y0, h, n_steps)
```