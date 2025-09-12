
import numpy as np

s_groups = [[
    4, 12, 20, 38, 56
],
    [1, 3, 11, 19, 37, 55]
]

rare_earths = [x for x in range(57, 72)] + [x for x in range(89, 95)]

d_groups = [
    [21, 39] + rare_earths
]

d_groups += [[x, x+18, x+50] for x in range(22, 31)]


d_groups_no_REAs = [
    [21, 39]
]

d_groups_no_REAs += [[x, x+18, x+50] for x in range(22, 31)]

p_groups = [[2]]
p_groups += [[x, x+8, x+26, x+44, x+76] for x in range(5, 8)]
p_groups += [[x, x+8, x+26, x+44] for x in range(8, 11)]

p_groups_flat = [item for col in p_groups for item in col]
s_groups_flat = [item for col in s_groups for item in col]
d_groups_flat = [item for col in d_groups for item in col]


all_groups = d_groups + p_groups + s_groups
all_groups_no_REAs = d_groups_no_REAs + p_groups + s_groups

symbols =\
    ["e", "H", "He",
     "Li", "Be", "B", "C", "N", "O", "F", "Ne",
     "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar",
     "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr",
     "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe",
     "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn",
     "Fr", "Ra", "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og"
     ]


toxic_elements = [33,48,24,82,80]

def env_friendly(r):
    s1 = set(r.numbers)
    s2 = set(rare_earths + toxic_elements)
    if len(s1.intersection(s2)) == 0:
        return True
    else:
        return False
  
def get_group(a):
    if a in d_groups_flat:
        return "d"
    elif a in s_groups_flat:
        return "s"
    elif a in p_groups_flat:
        return "p"
    else:
        print('Atomic number:',a)
        raise Exception('Wrong atomic number!')

def atomic_number_from_symbol(s:str):
    return np.where(np.array(symbols) == s)[0]