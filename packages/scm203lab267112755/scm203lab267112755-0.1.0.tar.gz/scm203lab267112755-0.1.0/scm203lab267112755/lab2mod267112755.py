from prettytable import PrettyTable

def runge_kutta2(f, t0, y0, h, n):
    """
    แก้สมการ ODE แบบ y' = f(t,y) โดยใช้ Runge-Kutta ลำดับที่ 2 (Heun method)
    Parameters
    f : function ฟังก์ชัน f(t,y)
    t0 : float ค่าเริ่มต้นของ t
    y0 : float ค่าเริ่มต้นของ y
    h : float ขนาดก้าว (step size)
    n : int จำนวนก้าวในการคำนวณ
    """
    t, y, i = [t0], [y0], 0
    table = PrettyTable(["Iter", "t", "y", "k1", "k2"])
    while i < n:
        k1 = f(t[-1], y[-1])
        k2 = f(t[-1]+h, y[-1]+h*k1)
        y_new = y[-1] + h*(k1+k2)/2
        t_new = t[-1] + h
        table.add_row([i, f"{t_new:.2f}", f"{y_new:.6f}", f"{k1:.6f}", f"{k2:.6f}"])
        y.append(y_new)
        t.append(t_new)
        i += 1
    print("\n[Runge-Kutta 2nd Order Results]")
    print(table)
    return t, y


def runge_kutta3(f, t0, y0, h, n):
    """
    แก้สมการ ODE แบบ y' = f(t,y) โดยใช้ Runge-Kutta ลำดับที่ 3
    f : function ฟังก์ชัน f(t,y)
    t0 : float ค่าเริ่มต้นของ t
    y0 : float ค่าเริ่มต้นของ y
    h : float ขนาดก้าว (step size)
    n : int จำนวนก้าวในการคำนวณ
    """
    t, y, i = [t0], [y0], 0
    table = PrettyTable(["Iter", "t", "y", "k1", "k2", "k3"])
    while i < n:
        k1 = f(t[-1], y[-1])
        k2 = f(t[-1]+h/2, y[-1]+h*k1/2)
        k3 = f(t[-1]+h, y[-1]-h*k1+2*h*k2)
        y_new = y[-1] + h*(k1+4*k2+k3)/6
        t_new = t[-1] + h
        table.add_row([i, f"{t_new:.2f}", f"{y_new:.6f}", f"{k1:.6f}", f"{k2:.6f}", f"{k3:.6f}"])
        y.append(y_new)
        t.append(t_new)
        i += 1
    print("\n[Runge-Kutta 3rd Order Results]")
    print(table)
    return t, y


if __name__ == "__main__":
    f = lambda t, y: y - t**2 + 1

    # Runge-Kutta 2nd order
    runge_kutta2(f, 0, 0.5, 0.5, 5)

    # Runge-Kutta 3rd order
    runge_kutta3(f, 0, 0.5, 0.5, 5)