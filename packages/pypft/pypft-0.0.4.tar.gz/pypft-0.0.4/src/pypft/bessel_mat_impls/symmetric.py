import numpy as np
from scipy.special import jv

def bessel_mat(samples, spokes):
    """Symmetric Bessel matrix calculation implementation. Based on the fact that ${J_{ - \alpha }}\left( x \right) = {\left( { - 1} \right)^\alpha }{J_\alpha }\left( x \right)$
    samples: integer, number of samples.
    spokes: integer, number of spokes. spokes must be even.
    
    return:
    bessel_mat: 2D numpy array, in the shape of (samples, spokes)."""
    assert type(samples) == int and samples > 0
    assert type(spokes) == int and spokes > 0
    assert spokes % 2 == 0 # spokes must be even

    cart_r = int(np.round(samples * np.sqrt(2)))

    bessel_mat_samples = cart_r * samples
    

    rho = (1 / 2 + np.arange(samples))/samples
    r = np.arange(1/2, cart_r+1/2, 1/2)
    bessel_r = np.pi * (rho[np.newaxis, :] * r[:, np.newaxis]).flatten()

    bessel_mat = np.zeros((bessel_mat_samples, spokes), "float64")

    order = spokes//2
    for j in np.arange(bessel_mat_samples):
        for ord_n in np.arange(order+1):
            bessel_mat[j, order-ord_n] = jv(-ord_n, bessel_r[j])
    
    bessel_mat[:, order+1:] = bessel_mat[:, order-1:0:-1] * np.expand_dims((-1)**np.arange(1,order), 0)

    return bessel_mat