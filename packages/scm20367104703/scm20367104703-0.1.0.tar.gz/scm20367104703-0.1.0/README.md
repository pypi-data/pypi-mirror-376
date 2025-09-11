# scm20367104703

`scm20367104703`is package to find Roots of eqaution

---

## Features
- **Fixed-Point Iteration**: use a function `fixed_point()` to use Fixed_point method
- **Secant Method**: use a function `secant()` to use Secant method
- **2nd-order Runge-Kutta**: `wating`
- **5nd-order Runge-Kutta** : `wating`
---

## Installation

You can install the package directly from PyPI:

```
pip install scm20367104703

```
---

## Example1
```
if __name__ == "__main__":
    def g(x):
        return (x**2 + 3) / 5
    initial_guess = 0.5
    root, iterations = fixed_point(g, initial_guess)
    print(f"\nApproximate: {root}")
    print(f"iterations: {iterations}")
```
---
## Example2
```
if __name__ == "__main__":
    def f(x):
        return x**3 - x - 2  
    root, iterations = secant(f, 1, 2)
    print(f"\nApproximate : {root}")
    print(f"iterations: {iterations}")
```