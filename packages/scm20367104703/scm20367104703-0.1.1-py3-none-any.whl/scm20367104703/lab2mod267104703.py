"""
This is module to solves an ordinary differential equation
- 2nd-order Runge-Kutta (Midpoint Method)
- 5th-order Runge-Kutta method
"""
from prettytable import PrettyTable

def rk2(f, t0, y0, h, n_steps):
    """
    2nd-order Runge-Kutta (Midpoint Method) สำหรับแก้สมการเชิงอนุพันธ์ y' = f(t, y)
    
    Parameters:
    f       : function - ฟังก์ชัน f(t, y)
    t0      : float    - ค่าเริ่มต้นของ t
    y0      : float    - ค่าเริ่มต้นของ y
    h       : float    - ขนาดก้าว (step size)
    n_steps : int      - จำนวนก้าวที่จะคำนวณ
    
    Returns:
    (list_t, list_y) : tuple of lists - ค่า t และ y ที่คำนวณได้ในแต่ละก้าว
    """
    t = t0
    y = y0
    list_t = [t]
    list_y = [y]
    
    table = PrettyTable()
    table.field_names = ["Step", "t", "y"]
    table.add_row([0, f"{t:.4f}", f"{y:.4f}"])
    
    for i in range(1, n_steps + 1):
        k1 = f(t, y)
        k2 = f(t + h/2, y + h/2 * k1)
        y = y + h * k2
        t = t + h
        
        list_t.append(t)
        list_y.append(y)
        table.add_row([i, f"{t:.4f}", f"{y:.4f}"])
    
    print(table)
    return list_t, list_y

#Test
if __name__ == "__main__":
    def f(t, y):
        return y - t**2 + 1
    
    t0 = 0.0
    y0 = 0.5
    h = 0.5
    n_steps = 8
    
    rk2(f, t0, y0, h, n_steps)


def rk5(f, t0, y0, h, n_steps):
    """
    5th-order Runge-Kutta method สำหรับแก้สมการเชิงอนุพันธ์ y' = f(t, y)
    
    Parameters:
    f       : function - ฟังก์ชัน f(t, y)
    t0      : float    - ค่าเริ่มต้นของ t
    y0      : float    - ค่าเริ่มต้นของ y
    h       : float    - ขนาดก้าว (step size)
    n_steps : int      - จำนวนก้าวที่จะคำนวณ
    
    Returns:
    (list_t, list_y) : tuple of lists - ค่า t และ y ที่คำนวณได้ในแต่ละก้าว
    """
    t = t0
    y = y0
    list_t = [t]
    list_y = [y]

    table = PrettyTable()
    table.field_names = ["Step", "t", "y"]
    table.add_row([0, f"{t:.6f}", f"{y:.6f}"])

    for i in range(1, n_steps + 1):
        k1 = h * f(t, y)
        k2 = h * f(t + h/4, y + k1/4)
        k3 = h * f(t + h/4, y + (k1 + k2)/8)
        k4 = h * f(t + h/2, y - k2/2 + k3)
        k5 = h * f(t + 3*h/4, y + (3*k1 + 9*k4)/16)
        k6 = h * f(t + h, y - (3*k1 + 9*k4)/7 + (8*k2 + 16*k3)/7)
        
        y = y + (7*k1 + 32*k3 + 12*k4 + 32*k5 + 7*k6) / 90
        t = t + h

        list_t.append(t)
        list_y.append(y)
        table.add_row([i, f"{t:.6f}", f"{y:.6f}"])

    print(table)
    return list_t, list_y

#Test
if __name__ == "__main__":
    def f(t, y):
        return y - t**2 + 1
    t0 = 0.0
    y0 = 0.5
    h = 0.5
    n_steps = 8
    rk5(f, t0, y0, h, n_steps)
