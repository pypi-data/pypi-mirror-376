"""
This is module to find roots of equation
- Fixed-Point Iteration Method
- Secant Method
"""
from prettytable import PrettyTable

def fixed_point(g, x0, tol=1e-6, max_iter=100):
    """
    Fixed-Point Iteration Method to find a root of equation x = g(x)
    
    Parameters:
    g       : function - ฟังก์ชัน g(x) ที่ใช้ในการคำนวณจุดคงที่
    x0      : float    - ค่าประมาณเริ่มต้น
    tol     : float    - ความแม่นยำที่ต้องการ (default 1e-6)
    max_iter: int      - จำนวนรอบการวนลูปสูงสุด (default 100)
    
    Returns:
    x       : float    - ค่ารากที่ประมาณได้
    n       : int      - จำนวนรอบการวนลูปที่ใช้
    """
    x = x0
    table = PrettyTable()
    table.field_names = ["Iteration", "x", "Error"]

    for n in range(1, max_iter + 1):
        x_new = g(x)
        error = abs(x_new - x)
        table.add_row([n, f"{x_new:.8f}", f"{error:.8f}"])
        if error < tol:
            print(table)
            return x_new, n
        x = x_new

    print(table)
    return x, n

#Test 
if __name__ == "__main__":
    def g(x):
        return (x**2 + 3) / 5
    initial_guess = 0.5
    root, iterations = fixed_point(g, initial_guess)
    print(f"\nApproximate: {root}")


def secant(f, x0, x1, tol=1e-6, max_iter=100):
    """
    Secant Method to find root of f(x) = 0
    
    Parameters:
    f       : function - ฟังก์ชันที่ต้องการหาคำตอบ
    x0, x1  : float    - ค่าประมาณเริ่มต้นสองค่า
    tol     : float    - ค่าความแม่นยำที่ต้องการ
    max_iter: int      - จำนวนรอบสูงสุด
    
    Returns:
    root    : float    - รากที่ประมาณได้
    n       : int      - จำนวนรอบที่ใช้
    """
    table = PrettyTable()
    table.field_names = ["Iteration", "x0", "x1", "x2", "Error"]
    
    for n in range(1, max_iter + 1):
        if f(x1) - f(x0) == 0:
            print("Error: Division by zero in secant method")
            break
        
        x2 = x1 - f(x1) * (x1 - x0) / (f(x1) - f(x0))
        error = abs(x2 - x1)
        
        table.add_row([n, f"{x0:.8f}", f"{x1:.8f}", f"{x2:.8f}", f"{error:.8f}"])
        
        if error < tol:
            print(table)
            return x2, n
        
        x0, x1 = x1, x2
    
    print(table)
    return x2, n

#To test function in module
if __name__ == "__main__":
    def f(x):
        return x**3 - x - 2

    root, iterations = secant(f, 1, 2)
    print(f"\nApproximate : {root}")
