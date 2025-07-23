# %%
from scikits.umfpack import spsolve
import numpy as np
import scipy as sp
import pickle
with open('/Users/michaelweinold/github/GreenGraph/dev/IminusAeco.pkl', 'rb') as f:
    IminusAeco = pickle.load(f)
A = IminusAeco.data.tocsr()
f = np.zeros(A.shape[0])
f[0] = 1.0


# %%
