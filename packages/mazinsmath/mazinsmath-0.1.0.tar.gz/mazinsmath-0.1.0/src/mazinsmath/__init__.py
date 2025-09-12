PI=3.141592653589793
TAU=6.283185307179586
E=2.718281828459045

def absf(x):
    return x if x>=0 else -x

def sgn(x):
    return 0 if x==0 else (1 if x>0 else -1)

def sqrt(x):
    if x<0: raise ValueError("sqrt domain")
    if x==0: return 0.0
    r=x
    for _ in range(60):
        r=0.5*(r+x/r)
    return r

def cbrt(x):
    if x==0: return 0.0
    r=x
    for _ in range(60):
        r=(2*r+x/(r*r))/3
    return r

def exp(x):
    n=32
    y=x/n
    term=1.0
    s=1.0
    k=1.0
    for _ in range(60):
        term*=y/k
        s+=term
        k+=1.0
        if absf(term)<1e-16: break
    r=1.0
    for _ in range(n):
        r*=s
    return r

def ln(x,tol=1e-12,max_iter=10000):
    if x<=0: raise ValueError("ln domain")
    k=0
    while x>2.0:
        x*=0.5
        k+=1
    while x<0.5:
        x*=2.0
        k-=1
    t=(x-1.0)/(x+1.0)
    power=t
    denom=1.0
    s=0.0
    for _ in range(max_iter):
        term=power/denom
        s+=term
        if absf(term)<tol: break
        power*=t*t
        denom+=2.0
    LN2=0.6931471805599453
    return 2.0*s+k*LN2

def log(x,base=None):
    return ln(x) if base is None else ln(x)/ln(base)

def powf(a,b):
    if a<=0: 
        if a==0 and b>0: return 0.0
        raise ValueError("pow domain")
    return exp(b*ln(a))

def deg2rad(d):
    return d*PI/180.0

def rad2deg(r):
    return r*180.0/PI

def _reduce_tau(x):
    k=int(x/TAU)
    x-=k*TAU
    if x>PI: x-=TAU
    if x<-PI: x+=TAU
    return x

def sin(x):
    x=_reduce_tau(x)
    x3=x*x*x
    x5=x3*x*x
    x7=x5*x*x
    x9=x7*x*x
    x11=x9*x*x
    return x - x3/6 + x5/120 - x7/5040 + x9/362880 - x11/39916800

def cos(x):
    x=_reduce_tau(x)
    x2=x*x
    x4=x2*x2
    x6=x4*x2
    x8=x4*x4
    x10=x8*x2
    return 1 - x2/2 + x4/24 - x6/720 + x8/40320 - x10/3628800

def tan(x):
    c=cos(x)
    if c==0: raise ValueError("tan undefined")
    return sin(x)/c

def atan(x):
    if absf(x)<=1:
        t=x
        x2=x*x
        s=t
        n=1
        while True:
            t*=-x2
            n+=2
            term=t/n
            s+=term
            if absf(term)<1e-16: break
        return s
    else:
        if x>0:
            return PI/2-atan(1/x)
        else:
            return -PI/2-atan(1/x)

def asin(x):
    if x<-1 or x>1: raise ValueError("asin domain")
    y=x
    for _ in range(50):
        y-= (sin(y)-x)/sqrt(1.0 - (sin(y))**2 + 1e-18)
    return y

def acos(x):
    return PI/2 - asin(x)

def sinh(x):
    ex=exp(x)
    exn=1.0/ex
    return 0.5*(ex-exn)

def cosh(x):
    ex=exp(x)
    exn=1.0/ex
    return 0.5*(ex+exn)

def tanh(x):
    ex=exp(x)
    exn=1.0/ex
    return (ex-exn)/(ex+exn)

def asinh(x):
    return ln(x+sqrt(x*x+1.0))

def acosh(x):
    if x<1: raise ValueError("acosh domain")
    return ln(x+sqrt(x*x-1.0))

def atanh(x):
    if x<=-1 or x>=1: raise ValueError("atanh domain")
    return 0.5*ln((1+x)/(1-x))

def floor(x):
    i=int(x)
    return i if i<=x else i-1

def ceil(x):
    i=int(x)
    return i if i>=x else i+1

def roundn(x,n=0):
    p=10**n
    return floor(x*p+0.5)/p

def factorial(n):
    if n<0 or int(n)!=n: raise ValueError("factorial domain")
    n=int(n)
    r=1
    for k in range(2,n+1):
        r*=k
    return r

def nCr(n,r):
    n=int(n); r=int(r)
    if r<0 or r>n: return 0
    r=min(r,n-r)
    num=1
    den=1
    for k in range(1,r+1):
        num*=n-r+k
        den*=k
    return num//den

def nPr(n,r):
    n=int(n); r=int(r)
    if r<0 or r>n: return 0
    p=1
    for k in range(n-r+1,n+1):
        p*=k
    return p

def gcd(a,b):
    a=abs(int(a)); b=abs(int(b))
    while b:
        a,b=b,a%b
    return a

def lcm(a,b):
    a=int(a); b=int(b)
    if a==0 or b==0: return 0
    return abs(a*b)//gcd(a,b)

def is_prime(n):
    n=int(n)
    if n<2: return False
    if n%2==0: return n==2
    if n%3==0: return n==3
    k=5
    while k*k<=n:
        if n%k==0 or n%(k+2)==0: return False
        k+=6
    return True

def next_prime(n):
    n=max(2,int(n)+1)
    while not is_prime(n):
        n+=1
    return n

def fib(n):
    n=int(n)
    a,b=0,1
    for _ in range(n):
        a,b=b,a+b
    return a

def mean(xs):
    s=0.0
    m=0
    for v in xs:
        s+=v
        m+=1
    return s/m if m else 0.0

def median(xs):
    ys=sorted(xs)
    n=len(ys)
    if n==0: return 0.0
    if n%2==1: return ys[n//2]
    return 0.5*(ys[n//2-1]+ys[n//2])

def variance(xs,ddof=0):
    m=mean(xs)
    s=0.0
    n=0
    for v in xs:
        d=v-m
        s+=d*d
        n+=1
    d=n-ddof
    if d<=0: return 0.0
    return s/d

def stdev(xs,ddof=0):
    return sqrt(variance(xs,ddof))

def clamp(x,a,b):
    return a if x<a else (b if x>b else x)

def signum(x):
    return sgn(x)

def map_range(x, a1,b1, a2,b2):
    return a2+(x-a1)*(b2-a2)/(b1-a1)

def diff(f,x,h=1e-6):
    return (f(x+h)-f(x-h))/(2*h)

def derivative(f,x,order=1,h=1e-6):
    if order==1: return diff(f,x,h)
    if order==2: return (f(x+h)-2*f(x)+f(x-h))/(h*h)
    g=lambda t: diff(f,t,h)
    return derivative(g,x,order-1,h)

def integral_trap(f,a,b,n=10000):
    if n<1: n=1
    h=(b-a)/n
    s=0.5*(f(a)+f(b))
    x=a
    for _ in range(1,n):
        x+=h
        s+=f(x)
    return s*h

def integral_simpson(f,a,b,n=10000):
    if n%2==1: n+=1
    h=(b-a)/n
    s=f(a)+f(b)
    x=a
    for i in range(1,n):
        x+=h
        s+= (4 if i%2==1 else 2)*f(x)
    return s*h/3

def newton(f,df,x0,tol=1e-12,max_iter=100):
    x=x0
    for _ in range(max_iter):
        y=f(x)
        d=df(x)
        if d==0: break
        x1=x-y/d
        if absf(x1-x)<tol: return x1
        x=x1
    return x

def bisection(f,a,b,tol=1e-12,max_iter=200):
    fa=f(a); fb=f(b)
    if fa==0: return a
    if fb==0: return b
    if fa*fb>0: raise ValueError("no bracket")
    for _ in range(max_iter):
        m=0.5*(a+b)
        fm=f(m)
        if absf(fm)<tol or 0.5*(b-a)<tol: return m
        if fa*fm<=0:
            b=fm and m or m
            fb=fm
        else:
            a=m
            fa=fm
    return 0.5*(a+b)

def solve_secant(f,x0,x1,tol=1e-12,max_iter=200):
    f0=f(x0); f1=f(x1)
    for _ in range(max_iter):
        if f1==f0: return x1
        x2=x1 - f1*(x1-x0)/(f1-f0)
        if absf(x2-x1)<tol: return x2
        x0,x1,f0,f1=x1,x2,f1,f(x2)
    return x1

def solve_quadratic(a,b,c):
    if a==0:
        if b==0: return []
        return [-c/b]
    d=b*b-4*a*c
    if d<0: return []
    if d==0: return [(-b)/(2*a)]
    s=sqrt(d)
    return [(-b-s)/(2*a), (-b+s)/(2*a)]

def poly_eval(coeffs,x):
    r=0.0
    for c in reversed(coeffs):
        r=r*x+c
    return r

def poly_add(a,b):
    n=max(len(a),len(b))
    r=[0]*n
    for i in range(n):
        ai=a[i] if i<len(a) else 0
        bi=b[i] if i<len(b) else 0
        r[i]=ai+bi
    return r

def poly_mul(a,b):
    r=[0]*(len(a)+len(b)-1)
    for i,ai in enumerate(a):
        for j,bj in enumerate(b):
            r[i+j]+=ai*bj
    return r

def poly_derivative(a):
    if len(a)<=1: return [0]
    return [i*a[i] for i in range(1,len(a))]

def poly_integral(a,c0=0.0):
    r=[c0]
    for i in range(len(a)):
        r.append(a[i]/(i+1))
    return r

def poly_roots_newton(a,x0,tol=1e-12,max_iter=200):
    f=lambda x: poly_eval(a,x)
    df=lambda x: poly_eval(poly_derivative(a),x)
    return newton(f,df,x0,tol,max_iter)

def mat_shape(A):
    return (len(A), len(A[0]) if A else 0)

def mat_eye(n):
    return [[1.0 if i==j else 0.0 for j in range(n)] for i in range(n)]

def mat_add(A,B):
    n,m=mat_shape(A)
    return [[A[i][j]+B[i][j] for j in range(m)] for i in range(n)]

def mat_sub(A,B):
    n,m=mat_shape(A)
    return [[A[i][j]-B[i][j] for j in range(m)] for i in range(n)]

def mat_mul(A,B):
    n,m=mat_shape(A)
    p,q=mat_shape(B)
    if m!=p: raise ValueError("shape mismatch")
    R=[[0.0]*q for _ in range(n)]
    for i in range(n):
        for k in range(m):
            aik=A[i][k]
            for j in range(q):
                R[i][j]+=aik*B[k][j]
    return R

def mat_t(A):
    n,m=mat_shape(A)
    return [[A[i][j] for i in range(n)] for j in range(m)]

def mat_det(A):
    n,m=mat_shape(A)
    if n!=m: raise ValueError("square required")
    M=[row[:] for row in A]
    det=1.0
    for i in range(n):
        piv=i
        for r in range(i+1,n):
            if absf(M[r][i])>absf(M[piv][i]): piv=r
        if absf(M[piv][i])<1e-18: return 0.0
        if piv!=i:
            M[i],M[piv]=M[piv],M[i]
            det=-det
        pivv=M[i][i]
        det*=pivv
        for r in range(i+1,n):
            f=M[r][i]/pivv
            for c in range(i,n):
                M[r][c]-=f*M[i][c]
    return det

def mat_inv(A):
    n,m=mat_shape(A)
    if n!=m: raise ValueError("square required")
    M=[row[:] for row in A]
    I=mat_eye(n)
    for i in range(n):
        piv=i
        for r in range(i+1,n):
            if absf(M[r][i])>absf(M[piv][i]): piv=r
        if absf(M[piv][i])<1e-18: raise ValueError("singular")
        if piv!=i:
            M[i],M[piv]=M[piv],M[i]
            I[i],I[piv]=I[piv],I[i]
        pivv=M[i][i]
        invp=1.0/pivv
        for c in range(n):
            M[i][c]*=invp
            I[i][c]*=invp
        for r in range(n):
            if r==i: continue
            f=M[r][i]
            if f!=0.0:
                for c in range(n):
                    M[r][c]-=f*M[i][c]
                    I[r][c]-=f*I[i][c]
    return I

def ascii_plot(f,xmin=-10,xmax=10,ymin=-10,ymax=10,width=80,height=25):
    W=width; H=height
    grid=[[" "]*W for _ in range(H)]
    for i in range(H):
        y=ymax-(ymax-ymin)*i/(H-1)
        if absf(y)<(ymax-ymin)/H:
            for j in range(W):
                grid[i][j]="-"
    for j in range(W):
        x=xmin+(xmax-xmin)*j/(W-1)
        if absf(x)<(xmax-xmin)/W:
            for i in range(H):
                grid[i][j]="|"
    ox=int((0 - xmin)*(W-1)/(xmax-xmin)) if xmin<=0<=xmax else None
    oy=int((ymax - 0)*(H-1)/(ymax-ymin)) if ymin<=0<=ymax else None
    if ox is not None and oy is not None and 0<=oy<H and 0<=ox<W:
        grid[oy][ox]="+"
    for j in range(W):
        x=xmin+(xmax-xmin)*j/(W-1)
        y=f(x)
        if y<ymin or y>ymax: continue
        i=int((ymax-y)*(H-1)/(ymax-ymin))
        if 0<=i<H and 0<=j<W:
            grid[i][j]="*"
    return "\n".join("".join(row) for row in grid)

def ascii_plot_parametric(fx,fy,tmin=0,tmax=TAU,width=80,height=25,pad=0.1,samples=1000):
    xs=[]; ys=[]
    for k in range(samples+1):
        t=tmin+(tmax-tmin)*k/samples
        x=fx(t); y=fy(t)
        xs.append(x); ys.append(y)
    xmin=min(xs); xmax=max(xs); ymin=min(ys); ymax=max(ys)
    dx=xmax-xmin; dy=ymax-ymin
    if dx==0: dx=1.0
    if dy==0: dy=1.0
    xmin-=pad*dx; xmax+=pad*dx; ymin-=pad*dy; ymax+=pad*dy
    def pf(x,y):
        return int((x-xmin)*(width-1)/(xmax-xmin)), int((ymax-y)*(height-1)/(ymax-ymin))
    grid=[[" "]*width for _ in range(height)]
    if xmin<=0<=xmax:
        j=int((0-xmin)*(width-1)/(xmax-xmin))
        for i in range(height):
            grid[i][j]="|"
    if ymin<=0<=ymax:
        i=int((ymax-0)*(height-1)/(ymax-ymin))
        for j in range(width):
            grid[i][j]="-"
    if xmin<=0<=xmax and ymin<=0<=ymax:
        j=int((0-xmin)*(width-1)/(xmax-xmin))
        i=int((ymax-0)*(height-1)/(ymax-ymin))
        grid[i][j]="+"
    for x,y in zip(xs,ys):
        j,i=pf(x,y)
        if 0<=i<height and 0<=j<width:
            grid[i][j]="*"
    return "\n".join("".join(row) for row in grid)

def sample_to_csv(f,xmin,xmax,n,filepath):
    if n<1: n=1
    h=(xmax-xmin)/n
    s="x,y\n"
    x=xmin
    for _ in range(n+1):
        y=f(x)
        s+=str(x)+","+str(y)+"\n"
        x+=h
    with open(filepath,"w") as fp:
        fp.write(s)
    return filepath

def find_roots_scan_bisect(f,x_min=-10.0,x_max=10.0,steps=1000,tol=1e-10):
    roots=[]
    xs=[x_min+i*(x_max-x_min)/steps for i in range(steps+1)]
    fs=[]
    for x in xs:
        try:
            fx=f(x)
        except:
            fx=float("nan")
        fs.append(fx)
    for i in range(steps):
        x0,x1=xs[i],xs[i+1]
        f0,f1=fs[i],fs[i+1]
        if isinstance(f0,float) and isinstance(f1,float):
            if f0!=f0 or f1!=f1: 
                continue
            if f0==0.0:
                root=x0
            elif f1==0.0:
                root=x1
            elif f0*f1<0:
                try:
                    root=bisection(f,x0,x1,tol=tol)
                except:
                    continue
            else:
                continue
            if all(absf(root-r)>1e-7 for r in roots):
                roots.append(root)
    roots.sort()
    return roots

def solve_linear(a,b):
    if a==0: return [] if b!=0 else ["inf"]
    return [-b/a]

def solve_cubic_real(a,b,c,d):
    if a==0: return solve_quadratic(b,c,d)
    A=b/a; B=c/a; C=d/a
    p=B - A*A/3
    q=2*A*A*A/27 - A*B/3 + C
    D=(q*q)/4 + (p*p*p)/27
    if D>0:
        u=-q/2 + sqrt(D)
        v=-q/2 - sqrt(D)
        u=powf(u,1/3) if u>=0 else -powf(-u,1/3)
        v=powf(v,1/3) if v>=0 else -powf(-v,1/3)
        x=u+v - A/3
        return [x]
    elif D==0:
        u=-q/2
        u=powf(u,1/3) if u>=0 else -powf(-u,1/3)
        x1=2*u - A/3
        x2=-u - A/3
        return [x1,x2]
    else:
        phi=acos(-q/(2*sqrt(-(p*p*p)/27)))
        r=2*sqrt(-p/3)
        x1=r*cos(phi/3)-A/3
        x2=r*cos((phi+2*PI)/3)-A/3
        x3=r*cos((phi+4*PI)/3)-A/3
        return [x1,x2,x3]
