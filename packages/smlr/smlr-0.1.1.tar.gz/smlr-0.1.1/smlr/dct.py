import numpy as np
from scipy.fftpack import dct, idct

def serialize(F, q):
    T = len(F)
    Fr = np.rot90(F.T)
    flat = np.array([Fr[-1,0]])
    for r in np.arange(2-T, T):
        d = np.diag(Fr, k=r)
        flat = np.concatenate((flat, d))
    return flat[:q]

def deserialize(c, T):
    G = np.zeros((T,T))
    q = len(c)
    ptr = 0
    cfull = np.zeros((T**2,))
    cfull[:q] = c
    for r in np.arange(1-T, T):
        elems = T - abs(r)
        G += np.diagflat(cfull[ptr:ptr+elems], k=r)
        ptr += elems
    return np.rot90(G, k=3).T


def encode_tile(f, q):
    Fdct = dct(dct(np.real(f), type=1, axis=1), type=1, axis=0)
    return serialize(Fdct, q)

def decode_tile(d, T):
    Fcdt = deserialize(d, T)
    norm = 2*(T**2)
    return idct(idct(np.real(Fcdt/norm), type=1, axis=1), type=1, axis=0) 

def encode_JPEG(f, T, q):
    h, w = np.shape(f)[:2]

    wtiles = np.arange(0, w-T+1, T)
    htiles = np.arange(0, h-T+1, T)

    G = np.zeros((len(htiles), len(wtiles), q))

    for C,c in enumerate(wtiles):
        for R,r in enumerate(htiles):
            ftile = f[r:r+T, c:c+T]
            G[R,C] = encode_tile(ftile, q)

    return G

def decode_JPEG(G, T):
    n_htiles, n_wtiles, _ = G.shape

    f = np.zeros( (T*n_htiles, T*n_wtiles) )

    wtiles = np.arange(0, np.shape(f)[1], T)
    htiles = np.arange(0, np.shape(f)[0], T)

    for C,c in enumerate(wtiles):
        for R,r in enumerate(htiles):
            f[r:r+T,c:c+T] = decode_tile(G[R,C],T)

    return f

def _compress_2d(f2d, r, T=8):
    """Compress a single-channel 2D image tile-wise using DCT."""
    if r <= 0:
        raise ValueError("ratio must be >= 1")
    q_value = int(round((T * T) / float(r)))
    q_value = max(1, min(T * T, q_value))
    return decode_JPEG(encode_JPEG(f2d, T, q_value), T)

def compress(f, r):
    """
    Compress an image using DCT.

    - If `f` is 2D (grayscale), compress directly.
    - If `f` is 3D with 3 or 4 channels, compress each of the first 3 channels independently
      and stack back into an RGB array.
    """
    if f.ndim == 2:
        return _compress_2d(f, r)
    if f.ndim == 3:
        h, w, c = f.shape
        if c < 3:
            return _compress_2d(f[..., 0], r)
        channels = [_compress_2d(f[..., i], r) for i in range(3)]
        return np.stack(channels, axis=2)
    raise ValueError("Unsupported image shape for DCT compression: %r" % (f.shape,))
