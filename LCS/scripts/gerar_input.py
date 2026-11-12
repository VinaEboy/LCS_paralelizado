import os

# pasta raiz do lcs
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "inputs", "small"))

### SMALL ###

dir_ex0 = os.path.join(base_dir, "ex0")
os.makedirs(dir_ex0, exist_ok=True)
path_ex0_a = os.path.join(dir_ex0, "fileA.in")
if not os.path.exists(path_ex0_a):
    f = open(path_ex0_a, "w")
    f.write("heagawghee\n")
    f.close()
path_ex0_b = os.path.join(dir_ex0, "fileB.in")
if not os.path.exists(path_ex0_b):
    f = open(path_ex0_b, "w")
    f.write("pawheae\n")
    f.close()


dir_ex1 = os.path.join(base_dir, "ex1")
os.makedirs(dir_ex1, exist_ok=True)
path_ex1_a = os.path.join(dir_ex1, "fileA.in")
if not os.path.exists(path_ex1_a):
    f = open(path_ex1_a, "w")
    f.write("aab"*1000 + "\n")
    f.close()
path_ex1_b = os.path.join(dir_ex1, "fileB.in")
if not os.path.exists(path_ex1_b):
    f = open(path_ex1_b, "w")
    f.write("aba"*1000 + "\n")
    f.close()

## BIG ## 