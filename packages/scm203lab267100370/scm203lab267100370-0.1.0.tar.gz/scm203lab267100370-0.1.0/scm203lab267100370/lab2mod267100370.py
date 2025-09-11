import math

def euler_method(f, x0,y0 ,xStop , h):
    data=[]
    x,y=x0,y0
    data.append([0,x,y])
    for i in range(1,n+1):
        y=y+h*f(x,y)
        x=x+h
        data.append([i,x,y])
    for row in data:
        print(row)
        
def kut4(f, x0, y0, xStop, h):
    data = []
    x, y = x0, y0
    data.append([0, x, y])
    for i in range(1, n + 1):
        k1 = h * f(x, y)
        k2 = h * f(x + h / 2, y + k1 / 2)
        k3 = h * f(x + h / 2, y + k2 / 2)
        k4 = h * f(x + h, y + k3)
        
        y = y + (k1 + 2 * k2 + 2 * k3 + k4) / 6
        x = x + h
        if x > xStop: break
            
        data.append([i, x, y])
    for row in data:
        print(row)
        
if __name__ == "__main__":
    f = lambda x,y: x + y
    x0, y0 = 0, 1
    xStop = 0.4
    h = 0.1
    n = int((xStop - x0) / h)
    
    print("Euler's Method:")
    euler_method(f, x0, y0, xStop, h)
    
    print("\nRunge-Kutta 4th Order Method:")
    kut4(f, x0, y0, xStop, h)