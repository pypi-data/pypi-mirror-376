from setuptools import setup, find_packages
import platform
import sys
import warnings
import subprocess
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

def check_windows_build_tools():
    """
    Check if Windows has the necessary build tools for compiling C extensions.
    Returns True if build tools are available, False otherwise.
    """
    # Check for cl.exe (Microsoft C++ compiler)
    try:
        result = subprocess.run(['where', 'cl'],
                              capture_output=True,
                              text=True,
                              shell=True)
        if result.returncode == 0:
            return True
    except:
        pass

    # Check common Visual Studio installation paths
    vs_paths = [
        r"C:\Program Files\Microsoft Visual Studio",
        r"C:\Program Files (x86)\Microsoft Visual Studio",
        r"C:\Program Files\Microsoft Visual C++",
        r"C:\Program Files (x86)\Microsoft Visual C++"
    ]

    for path in vs_paths:
        if os.path.exists(path):
            return True

    # Check if vcvarsall.bat exists (another indicator)
    try:
        result = subprocess.run(['where', 'vcvarsall.bat'],
                              capture_output=True,
                              text=True,
                              shell=True)
        if result.returncode == 0:
            return True
    except:
        pass

    return False

# Determine which requirements file to use
if platform.system() == "Windows":
    # Check if user has Visual C++ installed
    if check_windows_build_tools():
        req_file = "requirements.txt"  # Use full requirements if build tools available
        print("\n" + "="*60)
        print("Build tools detected. Installing with full dependencies.")
        print("="*60 + "\n")
    else:
        req_file = "requirements-windows.txt"  # Use Windows-friendly requirements
        warnings.warn(
            "\n" + "="*60 + "\n" +
            "WINDOWS INSTALLATION NOTE:\n" +
            "C++ build tools not detected. Using limited dependencies.\n" +
            "Some features (EIP-4844 blob transactions) will not be available.\n\n" +
            "For full feature support, please install Microsoft C++ Build Tools:\n" +
            "1. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/\n" +
            "2. Install with 'Desktop development with C++' workload\n" +
            "3. Restart your terminal and reinstall purechainlib\n\n" +
            "Or use the Windows-specific installation:\n" +
            "pip install purechainlib --no-deps\n" +
            "pip install -r requirements-windows.txt\n" +
            "="*60 + "\n",
            UserWarning
        )
else:
    req_file = "requirements.txt"

try:
    with open(req_file, "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    # Fallback to basic requirements if file not found
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="purechainlib",
    version="2.1.7",
    author="PureChain Team",
    author_email="dev@purechain.network",
    description="Python SDK for PureChain EVM network - Zero gas cost blockchain development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://pypi.org/project/purechainlib/",
    project_urls={
        "Documentation": "https://docs.purechain.network",
        "PyPI": "https://pypi.org/project/purechainlib/",
        "NPM Package": "https://www.npmjs.com/package/purechainlib",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: System :: Distributed Computing",
        "Topic :: Office/Business :: Financial",
        "Topic :: Security :: Cryptography",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        'web3': ['web3>=6.20.0,<7.0.0'],  # Optional: Full web3 support (requires C++ build tools on Windows)
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'pytest-cov>=4.0.0',
        ],
    },
    keywords=[
        "blockchain", "ethereum", "web3", "smart-contracts", 
        "zero-gas", "purechain", "evm", "solidity", "defi",
        "cryptocurrency", "web3py", "ethereum-development"
    ],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'purechain-security-setup=purechainlib.security_setup:main',
        ],
    },
)