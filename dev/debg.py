# %%
import pickle
with open('/Users/michaelweinold/github/GreenGraph/dev/graph.pkl', 'rb') as f:
    G = pickle.load(f)

M = G.generate_matrices(
    matrixformat='dense',
    generate_A=True,
    generate_B=True,
    generate_Q=False,
)