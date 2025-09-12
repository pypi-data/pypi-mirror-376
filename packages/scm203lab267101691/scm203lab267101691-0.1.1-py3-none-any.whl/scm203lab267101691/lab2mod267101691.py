"""
This is a docstring.
3-order Runge-Kutta method: solve the ODE y' = f(t, y) using the 3rd-order Runge-Kutta method.
4-order Runge-Kutta method: solve the ODE y' = f(t, y) using the 4th-order Runge-Kutta method.
"""

from prettytable import PrettyTable
def order_3_runge(f, a, b, N, y0):
    """
    This is a docstring.
    Solve the ODE y' = f(t, y) using the 3rd-order Runge-Kutta method.
    Parameters:
        f : The function f(t, y) defining the ODE
        a : left endpoint of interval
        b : right endpoint of interval
        N : The number of time
        y0 : The initial condition
    Returns:
        t_values : List of time values
        y_values : List of y values
    """
    h = (b - a) / N
    t = a
    y = y0
    t_values = [t]
    y_values = [y]
    i = 0
    myTable = PrettyTable(["i","ti","yi"])
    myTable.add_row([i, t, y])   
    while i < N:
        k1 = h * f(t, y)
        k2 = h * f(t + h/2, y + k1/2)
        k3 = h * f(t + h, y + k2)        
        y += (k1 + 4*k2 + k3) / 6
        t += h        
        t_values.append(f"{t:.1f}")
        y_values.append(y)
        i += 1
        myTable.add_row([i, f"{t:.1f}", y])
    print(myTable)
    return t_values, y_values

def order_4_runge(f, a, b, N, y0):
    """
    This is a docstring.
    Solve the ODE y' = f(t, y) using the 4th-order Runge-Kutta method.
    Parameters:
        f : The function f(t, y) defining the ODE
        a : left endpoint of interval
        b : right endpoint of interval
        N : The number of time
        y0 : The initial condition
    Returns:
        t_values : List of time values
        y_values : List of y values
    """
    h = (b - a) / N
    t = a
    y = y0
    t_values = [t]
    y_values = [y]
    i = 0
    myTable = PrettyTable(["i","ti","yi"])
    myTable.add_row([i, t, y])   
    while i < N:
        k1 = h * f(t, y)
        k2 = h * f(t + h/2, y + k1/2)
        k3 = h * f(t + h/2, y + k2/2)
        k4 = h * f(t + h, y + k3)        
        y += (k1 + 2*k2 + 2*k3 + k4) / 6
        t += h        
        t_values.append(f"{t:.1f}")
        y_values.append(y)
        i += 1
        myTable.add_row([i, f"{t:.1f}", y])
    print(myTable)
    return t_values, y_values

if __name__ == "__main__":
    print(order_3_runge(lambda t, y: y - t**2 + 1, 0, 2, 10, 0.5))
    print(order_4_runge(lambda t, y: y - t**2 + 1, 0, 2, 10, 0.5))