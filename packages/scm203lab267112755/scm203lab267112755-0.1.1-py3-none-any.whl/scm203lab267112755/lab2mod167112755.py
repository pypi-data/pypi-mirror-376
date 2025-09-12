from prettytable import PrettyTable

def secant(f, x0, x1, tol=1e-6, max_iter=100):
    """
     This a doc string secant method is parameter:
    f : function ฟังก์ชันเป้าหมาย
    x0, x1 : float ค่าเริ่มต้นสองค่าที่ใช้เริ่ม iteration
    tol : float, optional ค่าความเคลื่อนที่ยอมรับได้
    max_iter : int, optional จำนวนรอบ iteration สูงสุด (default = 100)
    """
    table = PrettyTable(["Iter", "x0", "x1", "x2", "f(x2)"])
    i = 0
    while i < max_iter:
        if f(x1) == f(x0): raise ZeroDivisionError("Division by zero in Secant method")
        x2 = x1 - f(x1)*(x1-x0)/(f(x1)-f(x0))
        table.add_row([i, f"{x0:.6f}", f"{x1:.6f}", f"{x2:.6f}", f"{f(x2):.6e}"])
        if abs(x2-x1) < tol:
            print("\n[Secant Method Result]")
            print(table)
            return x2
        x0, x1, i = x1, x2, i+1
    raise ValueError("Secant method did not converge")

def false_position(f, a, b, tol=1e-6, max_iter=100):
    """
    หาค่า root ของสมการ f(x) = 0 ด้วยวิธี False Position Method Parameters
    f : function ฟังก์ชันเป้าหมาย f(x)
    a, b : float ค่าช่วงเริ่มต้นที่ f(a)*f(b) < 0
    tol : float, optional ค่าความคลาดเคลื่อนที่ยอมรับได้ (default = 1e-6)
    max_iter : int, optional จำนวนรอบ iteration สูงสุด (default = 100)
    """
    if f(a)*f(b) > 0: raise ValueError("Same sign at endpoints")
    table = PrettyTable(["Iter", "a", "b", "c", "f(c)"])
    i = 0
    while i < max_iter:
        c = (a*f(b) - b*f(a)) / (f(b)-f(a))
        table.add_row([i, f"{a:.6f}", f"{b:.6f}", f"{c:.6f}", f"{f(c):.6e}"])
        if abs(f(c)) < tol:
            print("\n[False Position Method Result]")
            print(table)
            return c
        if f(a)*f(c) < 0: 
            b = c
        else: 
            a = c
        i += 1
    raise ValueError("False position method did not converge")

