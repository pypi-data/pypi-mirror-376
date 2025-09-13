# PyDRS - Sirius Power Supplies communication.

![Linting and Static](https://github.com/lnls-sirius/pydrs/actions/workflows/lint.yml/badge.svg)
![Latest tag](https://img.shields.io/github/tag/lnls-sirius/pydrs.svg?style=flat)
[![Latest release](https://img.shields.io/github/release/lnls-sirius/pydrs.svg?style=flat)](https://github.com/lnls-sirius/pydrs/releases)
[![PyPI version fury.io](https://badge.fury.io/py/pydrs.svg)](https://pypi.python.org/pypi/pydrs/)
[![Read the Docs](https://readthedocs.org/projects/spack/badge/?version=latest)](https://cnpem-sei.github.io/pydrs/)

## What is PyDRS?

**PyDRS** is a Python package based on the Basic Small Messages Protocol [**BSMP**](https://github.com/lnls-sirius/libbsmp). It is used to communicate with and command Sirius Current Power Supplies and its peripherals of the Digital Regulation System (**DRS**).
The tailored protocol specification for the power supplies can be found here [**DRS Communication Protocol**](https://cnpemcamp.sharepoint.com/:x:/s/ELP/EdITJFdE42hAgXubTjhZU3sBnd5BrOpUeI9EpaK4QO7mEQ?e=16i0pr).

Communication is established through RS-485, USB or Ethernet interfaces of the UDC (Universal Digital Controller) cards. For USB and Ethernet, there should be only used Application Layer of the BSMP protocol (defined as bsmp message), and for those cases the transport layer address bytes and checksum, shall be omitted.

In order to cover all DRS driven current power supplies whilst meeting models specificities, BSMP entities are standardized as follows:

1. **Common variables**: Variables used by all power supplies models, for example, general status and operating mode parameters. These variables occupy the first 25 BSMP variable Id's.
2. **Specific variables**: Each power supply model (chosen through the *PS Model* parameter) defines ID variables greater than 24 according to its application. Thus, when communicating with a power supply, its model should prior be known in order to correctly use the specifications of those BSMP variables. This includes measures of feedback and monitoring and also interlocks records.

## Basic Small Messages Protocol Library
The BSMP - Basic Small Messages Protocol - is a stateless, synchronous and lightweight protocol. It was designed to be used in serial communication networks of small embedded devices which contain a device with the role of a master.

This protocol manipulates 4 simple things, which are called Entities:

1. Variables
2. Groups
3. Curves
4. Functions

**Variables** can be either writable or read-only and have a value of up to 128 bytes.

A **Group** contains a bunch of Variables that can be read from or written to with only one command.

A **Curve** can be seen as a very large Variable, with up to 65536 blocks of 65520 bytes each.

Finally, a **Function** is a very simple way to perform a Remote Procedure Call (RPC).


## Prerequisites

 * [python==3.6](https://www.python.org/downloads/release/python-3612/)  **at least**
* pyserial==3.5
* numpy

**Disclaimer:** Although pydrs is tested up to [**Python 3.10.0**](https://www.python.org/downloads/release/python-3100/), you may want to check whether other apps dependant on it support Python 3.10.
Also, these other apps might depend on [**visualcppbuildtools**](https://visualstudio.microsoft.com/pt-br/visual-cpp-build-tools).


## Dev Utility scripts
Linux shell script to clear cache

```sh
sh ./scripts/clean.sh
```
## Installation Guide

### **User level:**
User-level version must be installed from the [**PyPI**](https://pypi.org/project/pydrs/) repository, using the 'pip install pydrs' command, which will install PyDRS onto the current Python path version.

### **Optional: Conda**

Conda is an open source package management system and environment management system that runs on Windows, macOS and Linux.

It can be used to create a specific environment where PyDRS module can be installed.
Use [**miniconda**](https://docs.conda.io/en/latest/miniconda.html#miniconda) for a free minimal installer for conda **or**
 [**anaconda**](https://conda.io/projects/conda/en/latest/user-guide/install/index.html) for a full version for Conda.

```command
conda create --name pydrs python=3.6
conda activate pydrs
```

```command
pip install -U pydrs
```

### **Developer level:**

For a developer level firstly clone the project repository from [**GitHub**](https://github.com/lnls-sirius/pydrs) to **your_local_folder** via git command:

```command
 git clone https://github.com/lnls-sirius/pydrs.git
```

![image](https://user-images.githubusercontent.com/19196344/139123128-3b70e4de-9bf3-4164-9e39-a3f8c2e64806.png)


Proceed to the **pydrs** folder and then you can use pip command by **two means** at your **choice**:

![image](https://user-images.githubusercontent.com/19196344/139126431-eae06bcd-81f9-4746-b8c5-2115f0637bab.png)


**1**. Just copying the repository locally. (Local changes on the project won't take effect on current pydrs installation).

Python module can be installed from the cloned source code. By using the 'pip install.' command at the root of the repository, the module will be installed normally, i.e. cloned files will be copied to the active python 'site-packages' folder.


```command
pip install .
```

![image](https://user-images.githubusercontent.com/19196344/139126660-0ce7cb62-8abe-492c-8596-1e581a061530.png)



**2**. Copying the repository locally with the update feature. (Local changes will immediately take effect on pydrs current installation).

The use of the '-e' flag in the local installation is recommended for situations where the code is under development and the changes are wanted to be used immediately. Installing it with the 'pip install -e.' command will link it to the repository folder, so package reinstallation won't be needed whenever a change in the active local repository occurs.

```command
pip install -e .
```
![image](https://user-images.githubusercontent.com/19196344/139126876-150791c2-9a94-4e75-b91c-28ace5002699.png)

### Tests

```command
pip install -e .[dev] -v
coverage run -m unittest discover
coverage xml
coverage report
```


## Usage

### Upgrading

- `drs.set_slave_add` and `drs.get_slave_add` were replaced by a property. Set the slave address with `drs.slave_addr = 5` and get with `address = drs.slave_addr`
- `drs.set_timeout` and `drs.get_timeout` are also proprerties. Set with `drs.timeout = 5` and get with `timeout = drs.timeout`
- `drs.closed_loop` is now `drs.close_loop` (verb form) to indicate that is an action.
- `drs.get_param_bank` returns a dictionary instead of a nested list. Printing behavior stays the same.
- `drs.read_vars_x` functions return a dictionary.
- All commands run through validation. In case validation fails, a descriptive exception will be raised, which can be used to trace the problem.
- Connecting to a given device is done during instantiation of the class. This means that instead of running `drs = pydrs.SerialDRS()` and then `drs.connect()`, you should run `drs = pydrs.SerialDRS("COM1", 3000000)` for example.
- `drs.read_vars_fac_n` was deprecated in favor of reading the vars you want through either `read_vars_fac_acdc` or `read_vars_fac_dcdc` to avoid confusion.
- `drs.read_vars_x` functions no longer implicitly loop or print, in favor of higher throughput and less confusion when scripting.
- Variables are read using variable groups, improving performance massively (93% reduction in read time). This means that if you attempt to read variables for a power supply type that doesn't correspond to the current power supply's type, it will most likely raise a "size mismatch" (`SerialInvalidPckgLen`) exception.

### Basic utilization

```python
>>> import pydrs # Import the module
>>> drs = pydrs.GenericDRS("10.0.6.64", 5000) # Connect to a device. It will automatically detect whether this is a serial or TCP/IP connection

 pyDRS - compatible UDC firmware version: 0.44 2022-06-30

>>> drs.slave_addr = 5 # Set slave address (optional)
>>> drs.read_ps_status() # Run your command
{'state': 'Off', 'open_loop': 0, 'interface': 0, 'active': 1, 'model': 'FBP', 'unlocked': 0}
```
