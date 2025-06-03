# %%
# example of single threaded matrix solver
from os import environ
environ['OMP_NUM_THREADS'] = '1'
from time import time
from numpy.random import rand
from numpy.linalg import solve
# record the start time
start = time()
# size of arrays
n = 8000
# create matrix
a = rand(n, n)
# create result
b = rand(n, 1)
# solve least squares equation
x = solve(a, b)
# calculate and report duration
duration = time() - start
print(f'Took {duration:.3f} seconds')

# %%

# example of multithreaded matrix solver
from os import environ
environ['OMP_NUM_THREADS'] = '8'
from time import time
from numpy.random import rand
from numpy.linalg import solve
# record the start time
start = time()
# size of arrays
n = 8000
# create matrix
a = rand(n, n)
# create result
b = rand(n, 1)
# solve least squares equation
x = solve(a, b)
# calculate and report duration
duration = time() - start
print(f'Took {duration:.3f} seconds')

# %%

import numpy as np
import math
def f(x):
    print(x)
    y = [1]*10000000
    [math.exp(i) for i in y]
def g(x):
    print(x)
    y = np.ones(10000000)
    np.exp(y)

# %%

from handythread import foreach
from processing import Pool
from timings import f,g
def fornorm(f,l):
    for i in l:
        f(i)
time fornorm(g,range(100))
time fornorm(f,range(10))
time foreach(g,range(100),threads=2)
time foreach(f,range(10),threads=2)
p = Pool(2)
time p.map(g,range(100))
time p.map(f,range(100))

# %%

import time # Make sure time is imported at the top of your script

# --- Placeholder definitions for 'g' and 'fornorm' ---
# Replace these with your actual definitions in dev_paralell.py
# If 'g' and 'fornorm' are already defined in your script before line 65,
# you might not need these placeholders here.

def fornorm(data, iterations_range):
    """
    Placeholder for your fornorm function.
    Replace this with your actual implementation.
    """
    print(f"Executing fornorm with data: '{data}' for {len(list(iterations_range))} iterations.")
    # Simulate some work
    time.sleep(0.5) # e.g., 0.5 seconds of work
    return "result from fornorm"

g = "some_sample_data_for_g"
# --- End of placeholder definitions ---

# Corrected way to call and time your 'fornorm' function
# This would replace line 65 in your script.
print("Preparing to call and time the 'fornorm' function...")
start_fornorm_time = time.time()
try:
    # Ensure 'g' and 'fornorm' are defined by this point
    result_from_fornorm = fornorm(g, range(100))
    duration_fornorm = time.time() - start_fornorm_time
    print(f"Call to 'fornorm(g, range(100))' took {duration_fornorm:.3f} seconds.")
    print(f"Result from fornorm: {result_from_fornorm}")
except NameError as e:
    print(f"Execution Error: {e}. Please ensure 'g' and 'fornorm' are defined before use.")
except Exception as e:
    print(f"An unexpected error occurred during 'fornorm' execution: {e}")

print("-" * 30)