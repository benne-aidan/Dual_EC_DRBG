import gmpy2 as op

# Elliptic curve, parameterized by coefficients a, b, and modulus of field
# No more information is needed as Dual_EC_DRBG always uses a field with prime modulus
class EC:
    def __init__(self, a, b, mod):
        self.a = a
        self.b = b
        self.mod = mod

# Point on elliptic curve, parameterized by curve and x/y-coordinates
class point:
    def __init__(self, curve, x, y):
        self.curve = curve
        self.x = x
        self.y = y
    
    # Scalar multiplication by a (int)
    def scalar_mult(self, a):
        # Identity and 0 cases
        if a == 0 or self is None:
            return None
        elif a == 1:
            return self
        
        # Main case ('square and multiply')
        result = None
        current = self
        
        a = op.mod(a, self.curve.mod)
        while a > 0:
            if a % 2 == 1:
                result = add_points(result, current)
            current = add_points(current, current)
            a >>= 1
            
        return result


# Bit generator, parameterized by seed (s0), and two points P and Q on elliptic curve E
class DRBG:
    # For points P, Q on elliptic curve E
    def __init__(self, seed, P, Q, E):
        self.state = seed
        self.P = P
        self.Q = Q
        self.E = E
    
    # Check that P, Q lie on E
    def validate(self):
        p = self.E.mod
        for point in [self.P, self.Q]:
            left = op.powmod(point.y, 2, p)
            x3 = op.powmod(point.x, 3, p)       # x^3
            ax = op.mod(op.mul(self.E.a, point.x), p)
            right = op.mod(op.add(op.add(x3, ax), self.E.b), p)
            if left != right:
                print('ERROR: Point-curve validation insuccessful')
                exit(1)
        return
        
    
    def rand(self):
        self.state = (self.P.scalar_mult(self.state)).x
        r = self.Q.scalar_mult(self.state).x
        

# `none` is used to represent point at infinity (group identity element). It must be checked for.
def add_points(P, Q, E):
    # Handle identity case
    if P is None:
        return Q
    if Q is None:
        return P
    
    # P and Q are inverses; return identity
    if P.x == Q.x and P.y == -Q.y:
        return None
    

    # Otherwise, compute slope between two points (or tangent line if P = Q)
    p = E.mod
    slope = None
    if P.x == Q.x and P.y == Q.y:   # P = Q
        numerator = op.mod(op.add(op.mul(3, op.powmod(P.x, 2, p)), E.a), p)
        denominator = op.invert(op.mod(op.mul(2, P.y), p), p)
        slope = op.mod(op.mul(numerator, denominator), p)
    else:   # P != Q
        numerator = op.mod(op.sub(Q.y, P.y), p)
        denominator = op.invert(op.mod(op.sub(Q.x, P.x), p), p)
        slope = op.mod(op.mul(numerator, denominator), p)
    
    # Computing x, y coordinates of sum
    x3 = op.mod(op.sub(op.sub(op.powmod(slope, 2, p), P.x), Q.x), p)
    y3 = op.mod(op.sub(op.mod(op.mul(slope, op.sub(P.x, x3)), p), P.y), p)
    
    # Define and return new point
    sum = point(E, x3, y3)
    return sum

# Truncate x-coord, default m=16 per NIST standard
def truncate(x, bits=256, m=16):
    mask = (1 << (bits - m)) - 1
    truncated = x & mask
    return truncated


x = 85
print(truncate(x, 8, 4))