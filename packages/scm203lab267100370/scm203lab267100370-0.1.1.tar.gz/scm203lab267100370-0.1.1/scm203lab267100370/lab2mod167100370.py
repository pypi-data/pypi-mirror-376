import math

def bisection(f, a, b,nMax,TOL):
    data = []
    if f(a) * f(b) > 0:
        print("No root in the given interval")
        return None
    
    c_old = None
    for i in range(nMax + 1):
        c = (a + b) / 2
        
        error = abs(c - c_old) if c_old is not None else None
        data.append([i, c, error])
        
        if f(c) == 0 or (error is not None and error < TOL):
            print("root = ", c)
            break
        
        if f(a) * f(c) < 0:
            b = c
        else:
            a = c
        
        c_old = c
        if i == nMax : print("root is not found.")
    for row in data:
        print(row)

def fixpoint(g, x0, nMax, TOL):
    data = []
    x_old = None
    for i in range(nMax + 1):
        x = g(x_old) if i > 0 else x0
        
        error = abs(x - x_old) if x_old is not None else None
        data.append([i, x, error])
        
        if error is not None and error < TOL:
            print("root = ", x)
            break
        
        x_old = x
        if i == nMax : print("root is not found.")
    for row in data:
        print(row)



if __name__ == "__main__":
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
