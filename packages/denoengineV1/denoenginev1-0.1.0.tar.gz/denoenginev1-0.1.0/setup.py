from setuptools import setup, find_packages

setup(
    name="denoengineV1",
    version="0.1.0",
    description="Basit bir 3D oyun motoru (OpenGL + GLFW)",
    author="DenoTUBE",
    packages=find_packages(),
    install_requires=[
        "PyOpenGL",
        "glfw"
    ],
    python_requires=">=3.8",
)
