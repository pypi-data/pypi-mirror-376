from setuptools import setup, find_packages

setup(
    name="pyvirtualmachine",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "PySimpleGUI",
    ],
    entry_points={
        "console_scripts": [
            "pyvm=pyvirtualmachine.gui:main",
        ],
    },
    python_requires=">=3.8",
    author="TuFueguito",
    description="Run and manage virtual machines with Python and VirtualBox",
    url="https://github.com/fueguitos/pyvirtualmachine",
)
