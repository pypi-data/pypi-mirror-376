from setuptools import setup
from Cython.Build import cythonize
import os

tmp='/tmp/encode'
root=os.path.dirname(tmp)

setup(
    package_dir={"": root},
    name='encryptcode',
    ext_modules=cythonize("%s/encryptcode.py" %tmp),
)    
