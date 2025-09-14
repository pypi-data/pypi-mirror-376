
from setuptools import setup, find_packages
setup(
    name="DenoEngine",
    version="0.3.0",
    description="Tam özellikli 3D engine (FPS/TPS + 2D HUD + Physics)",
    packages=find_packages(),
    install_requires=["PyOpenGL","glfw","PyOpenGL_accelerate"],
    python_requires=">=3.8"
)
