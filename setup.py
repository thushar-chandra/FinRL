from __future__ import annotations

from setuptools import find_packages
from setuptools import setup

# Read requirements.txt, ignore comments
try:
    REQUIRES = list()
    f = open("requirements.txt", "rb")
    for line in f.read().decode("utf-8").split("\n"):
        line = line.strip()
        if "#" in line:
            line = line[: line.find("#")].strip()
        if line:
            REQUIRES.append(line)
except FileNotFoundError:
    print("'requirements.txt' not found!")
    REQUIRES = list()

setup(
    name="ca-marl",
    version="2.0.0",
    include_package_data=True,
    license="MIT",
    packages=find_packages(),
    description="CA-MARL: Confidence-Aware Multi-Agent Reinforcement Learning for Portfolio Decision Support",
    long_description="Research framework for confidence-aware multi-agent reinforcement learning in portfolio allocation.",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Office/Business :: Financial",
    ],
    keywords="Reinforcement Learning, Finance, Portfolio Management",
    platform=["any"],
    python_requires=">=3.11",
)
