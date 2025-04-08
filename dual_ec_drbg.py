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
                result = add_points(result, current, self.curve)
            current = add_points(current, current, self.curve)
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
            if point is None:
                print('ERROR: Point cannot be None')
                exit(1)
            left = op.powmod(point.y, 2, p)
            x3 = op.powmod(point.x, 3, p)       # x^3
            ax = op.mod(op.mul(self.E.a, point.x), p)
            right = op.mod(op.add(op.add(x3, ax), self.E.b), p)
            if left != right:
                print('ERROR: Point-curve validation unsuccessful')
                exit(1)
        return
        
    # Function for generating next bit sequence
    def rand(self):
        new_point = self.P.scalar_mult(self.state)
        
        # this should never happen
        if new_point is None:
            print('ERROR: Invalid state')
            exit(1)

        self.state = new_point.x
        r_point = self.Q.scalar_mult(self.state)

        # this should also never happen
        if r_point is None:
            print('ERROR: Invalid random point')
            exit(1)

        r = r_point.x
        truncated = truncate(r)

        # i dont know how this would even be possible
        if truncated >= (1 << (256 - 16)):
            print('WARNING: Truncated value exceeds expected range')
        return truncated
        

# `none` is used to represent point at infinity (group identity element). It must be checked for.
def add_points(P, Q, E=None):
    # Use P's curve if E not provided
    if E is None and P is not None:
        E = P.curve
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

def enumerate_untruncated_x(truncated_x, bits=256, m=16):
    # number of bits kept after truncation
    kept_bits = bits - m
    mask = (op.mpz(1) << kept_bits) - 1
    
    # check correct input size
    if truncated_x > mask:
        print("ERROR: x-coordinate exceeds expected length")
    
    # generate all possible 16-bit prefixes
    candidates = []
    for prefix in range(0, 1 << m):
        candidate = (op.mpz(prefix) << kept_bits) | truncated_x
        candidates.append(candidate)
    
    return candidates

# Runs Dual_EC_DRBG according to specification
def run_spec_gen(amt=10, range=10):
    seed = op.mpz(0xC49D360886E704936A6678E1139D26B7819F7E90)
    a_spec = op.mpz(0xffffffff00000001000000000000000000000000fffffffffffffffffffffffc)
    b_spec = op.mpz(0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b)
    p_spec = op.mpz(0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff)
    curve_spec = EC(a_spec, b_spec, p_spec)

    P_x = op.mpz(0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296)
    P_y = op.mpz(0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5)
    P = point(curve_spec, P_x, P_y)

    Q_x = op.mpz(0xc97445f45cdef9f0d3e05e1e585fc297235b82b5be8ff3efca67c59852018192)
    Q_y = op.mpz(0xb28ef557ba31dfcbdd21ac46e2a91e3c304f44cb87058ada2cb815151e610046)
    Q = point(curve_spec, Q_x, Q_y)

    gen = DRBG(seed, P, Q, curve_spec)
    gen.validate()
    for i in range(amt):
        print(gen.rand() % range)

# Maliciously chooses d
def backdoor():
    seed = op.mpz(0xC49D360886E704936A6678E1139D26B7819F7E90)
    a_spec = op.mpz(0xffffffff00000001000000000000000000000000fffffffffffffffffffffffc)
    b_spec = op.mpz(0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b)
    p_spec = op.mpz(0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff)
    curve_spec = EC(a_spec, b_spec, p_spec)

    Q_x = op.mpz(0xc97445f45cdef9f0d3e05e1e585fc297235b82b5be8ff3efca67c59852018192)
    Q_y = op.mpz(0xb28ef557ba31dfcbdd21ac46e2a91e3c304f44cb87058ada2cb815151e610046)
    Q = point(curve_spec, Q_x, Q_y)

    # randomly chosen
    d = op.mpz(0x5FFCFE1A5F2AFBC7E9147F91F5A2C)
    P = Q.scalar_mult(d)

    gen = DRBG(seed, P, Q, curve_spec)
    gen.validate()





backdoor()
