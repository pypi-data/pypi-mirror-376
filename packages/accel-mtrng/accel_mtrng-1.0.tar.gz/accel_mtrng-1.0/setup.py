from setuptools import setup, Extension
import pybind11
import os

compile_args = ['-std=c++17', '-static-libgcc', '-static-libstdc++', '-Ofast']
link_args = ['-static']

root_dir = os.path.dirname(os.path.abspath(__file__))

ext_modules = [
    Extension(
        'accel_mtrng',
        ['randomizer.cpp', 'bindings.cpp'],
        include_dirs=[
            pybind11.get_include(),
            os.path.join(root_dir, ".")
        ],
        language='c++',
        extra_compile_args=compile_args,
        extra_link_args=link_args,
    ),
]

setup(
    name='accel_mtrng',
    version='1.0',
    author='surya narayan',
    description='Python bindings for a high-performance C++ random number library',
    ext_modules=ext_modules,
)