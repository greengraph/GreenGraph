# %%
import pickle
with open('/Users/michaelweinold/github/GreenGraph/dev/Geco.pkl', 'rb') as f:
    Geco = pickle.load(f)

Meco = Geco.generate_matrices(
    matrixformat='csr',
    generate_A=True,
    generate_B=True,
    generate_Q=False,
)

# %%



with open('/Users/michaelweinold/github/GreenGraph/dev/IminusAeco.pkl', 'wb') as f:
    pickle.dump(Meco.matrices['I-A'], f)


# %%
import pickle
import torch
import numpy as np
with open('/Users/michaelweinold/github/GreenGraph/dev/IminusAeco.pkl', 'rb') as f:
    IminusAeco = pickle.load(f)

Acsr = IminusAeco.data.tocsr()

f = np.zeros(IminusAeco.shape[0])
f[0] = 1.0

torch.sparse.spsolve(Acsr, f)