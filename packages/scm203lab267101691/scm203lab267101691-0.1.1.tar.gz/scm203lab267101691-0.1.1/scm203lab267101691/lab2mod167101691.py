"""
This is a docstring.
Bisection method: find root of f in [a,b] with error tolerance.
Newton's method: find root of f with initial guess x0 and error tolerance.
"""

from prettytable import PrettyTable
def bisection(f,a,b,error,nmax):
    """
    This is a docstring.
    Bisection medthod is finding root of f in [a,b] with error tolerance. 
    parameters:
        f: function for which to find root
        a: left endpoint of interval
        b: right endpoint of interval
        error: error tolerance
        nmax: maximum number of iterations
        returns: root of f or None if no root found in interval or if it reaches maximum iterations but result is more than error tolerance
    """
    myTable = PrettyTable(["i", "x[i]", "error"])
    if f(a)*f(b)>0:
        return None
    else:
        i = 0
        FA = f(a)
        while i < nmax:
            p = a + (b - a)/2
            FP = f(p)   
            myTable.add_row([i, p, abs(b - a)/2])
            if FP == 0 or (b-a)/2 < error:
                print(myTable)
                return p
            i += 1
            if FA*FP > 0:
                a = p
                FA = FP
            else:
                b = p
        print(myTable)
        return None

def newton(f,df,x0,error,nmax):
    """
    This is a docstring.
    Newton's method is finding root of f with initial guess x0 and error tolerance.
    parameters:
        f: function for which to find root
        df: derivative of f
        x0: initial guess
        error: error tolerance
        nmax: maximum number of iterations
        returns: root of f or None if it reaches maximum iterations but result is more than error tolerance
    """
    i = 0
    myTable = PrettyTable(["i", "x[i]", "error"])
    while i < nmax:
        x = x0 - f(x0)/df(x0)
        myTable.add_row([i, x, abs(x - x0)])
        if abs(x - x0) < error:
            print(myTable)
            return x
        i += 1
        x0 = x
    print(myTable)
    return None
    
if __name__ == "__main__":
    print("bisection ≈",bisection(lambda x: x**3+x-1,0,1,0.001,10))
    print("newton ≈",newton(lambda x: x**3+x-1,lambda x: 3*x**2+1,1,0.001,10))
