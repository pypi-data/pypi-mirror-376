<img src="./assets/logo.svg" width="200px">

# Oganesson

`oganesson` (`og` for short) is a python package that enables you to apply artificial intelligence workflows to your material discovery projects.

## Installation

`og` requires the installation of the following library:

- DGL: https://www.dgl.ai/pages/start.html

After installing the above library, you can install `og` using the `pip` command as follows:

`pip install oganesson`

# Features

`og` is currently under active development. The following features are currently available.

## Machine learning descriptors

`og` will bring together machine learning descriptors for materials and molecules within a unified framework. `og` currently provides the following descriptors:

- The BACD, ROSA and SymmetryFunctions introduced in this [publication](https://doi.org/10.1186/s13321-022-00658-9)
- Most of the descriptors from [DScribe](https://github.com/SINGROUP/dscribe)

Each descriptor has its own class, which extends the `Descriptors` class in the `oganesson.descriptors` module. Here is an example of how to describe a structure using the `BACD` and `SymmetryFunctions` descriptor classes.

```python
from oganesson.descriptors import BACD, SymmetryFunctions
from oganesson.ogstructure import OgStructure

bacd = BACD(OgStructure(file_name='examples/structures/Li3PO4_mp-13725.cif'))
print(bacd.describe())

sf = SymmetryFunctions(OgStructure(file_name='examples/structures/Li3PO4_mp-13725.cif'))
print(sf.describe())
```

## Genetic algorithms

The main purpose of `og` is to make complex artificial intelligence workflows easy to compose. Here is an example: running a genetic search for structures, where the structure optimization is performed using the M3GNET neural network model.

```python
from oganesson.genetic_algorithms import GA
ga = GA(species=['Na']*4 + ['H']*4)
for i in range(10):
    ga.evolve()
```

## Generation of the diffusion path for NEB calculations

The most painful part of doing transition state calculations in VASP is in building the images. The following code makes this happen in 2 lines of code. You only need to specify the structure file, and the atomic species you want to diffuse, and OgStructure will generate a folder for each path, and then write the POSCAR image files in each of these folders.

In the following example, we explore the possible Li diffusion paths in Li3PO4, given there are 6 Li atoms in the cell.

```python
from oganesson.ogstructure import OgStructure
og = OgStructure(file_name='examples/structures/Li3PO4_mp-13725.cif')
og.generate_neb('Li')
```
Note that the default value of `r`, which is 3, is sufficient for lithium systems. However, for the case of larger atoms such as Na, a larger value of `r` would be required.

## Finding a reasonable adsorption site of an atom on a surface

```python
from oganesson.ogstructure import OgStructure
og=OgStructure(file_name='examples/structures/MoS2.vasp')
og.add_atom_to_surface('Li').structure.to('MoS2_Li.vasp','poscar')
```