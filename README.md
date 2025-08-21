# (Py)UVM Testbench

This project sets up a comprehensive simulation environment for SystemVerilog RTL using CocoTB and PyUVM. The project implements and verifies an ALU (Arithmetic Logic Unit) design with ready/valid handshaking protocol using industry-standard verification methodologies.

## Features

- **SystemVerilog ALU** with 9 different operations and ready/valid protocol
- **PyUVM-based testbench** with complete verification environment
- **Code and functional coverage** support with Verilator
- **Regression testing** framework
- **Verification dashboard** for results visualization
- **Multiple test types** including directed and constrained random tests
- **Random-stable stimulus generation** for reproducible randomized tests

## Project Structure

```
uvm-tb/
├── rtl/
│   └── dut.sv              # SystemVerilog ALU implementation
├── tb/
│   ├── env/
│   │   ├── __init__.py
│   │   ├── env.py          # UVM environment components
│   │   └── utils.py        # Utility functions and enums
│   └── tests/
│       ├── __init__.py
│       ├── base_test.py    # Base test class
│       ├── simple_test.py  # Basic ALU test
│       ├── add_test.py     # Addition-focused test
│       ├── sequences.py    # Test sequences
│       └── regression.txt  # Regression test list
├── sim/                    # Simulation output directory
├── Makefile               # Main simulation Makefile
├── cocotb.mk             # CocoTB-specific Makefile
├── requirements.txt      # Python dependencies
├── verif_dashboard.py    # Verification dashboard generator
└── README.md            # Project documentation
```

## Setup Instructions

### Prerequisites

- **Verilator** (for simulation)
- **GTKWave** (for waveform viewing)
- **Python 3.8+** (preferably 3.12)
- **Git** (for version control)

### Installation Steps

1. **Create a Conda Environment** (recommended):
   ```bash
   conda create -n sv_cocotb_env python=3.12
   conda activate sv_cocotb_env
   ```

2. **Install Dependencies**:
   Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Installation**:
   Check that Verilator is installed:
   ```bash
   verilator --version
   ```

## Running Simulations

### Basic Simulation
Run a single test with default settings:
```bash
make sim
```

Run a specific test:
```bash
make sim TEST=add_test
```

### Advanced Options
Run with custom seed and log level:
```bash
make sim TEST=simple_test SEED=42 LOG_LEVEL=DEBUG
```

Enable waveform dumping:
```bash
make sim WAVES=1
```

Enable code coverage:
```bash
make sim COVERAGE_EN=1
```

### Regression Testing
Run all tests in the regression suite:
```bash
make regression
```

### View Results
View waveforms (requires GTKWave):
```bash
make view_waves TEST=simple_test SEED=1
```

Generate verification dashboard:
```bash
make verif_dashboard
```

## Available Make Commands

| Command | Description |
|---------|-------------|
| `make sim` | Run the default simulation (simple_test) |
| `make sim TEST=<test_name>` | Run a specific test |
| `make regression` | Run all tests in regression suite |
| `make view_waves` | View waveforms for the last simulation |
| `make verif_dashboard` | Generate verification results dashboard |
| `make clean` | Clean simulation files and Python cache |
| `make help` | Show help message with available options |

## Environment Variables

The following variables can be customized when running make:

| Variable | Default | Description |
|----------|---------|-------------|
| `SIM` | `verilator` | Simulation tool (verilator supported) |
| `TEST` | `simple_test` | Python module containing PyUVM tests |
| `SEED` | `1` | Random seed for simulation |
| `LOG_LEVEL` | `INFO` | CocoTB log level (DEBUG, INFO, WARNING, ERROR) |
| `WAVES` | `0` | Enable waveform dumping (0=off, 1=on) |
| `COVERAGE_EN` | `0` | Enable code and functional coverage collection (0=off, 1=on) |
| `TOPLEVEL_LANG` | `verilog` | Language of the top-level module |
| `VERILOG_SOURCES` | `rtl/*.sv` | Path to Verilog/SystemVerilog sources |
| `TOPLEVEL` | `alu` | Name of the top-level module |

## ALU Implementation Details

The ALU module (`rtl/dut.sv`) implements a 32-bit arithmetic logic unit with:

### Interface
- **Clock and Reset**: `clk_i`, `arst_n_i` (active-low async reset)
- **Input Interface**: Ready/valid handshaking with `valid_i`, `ready_o`
- **Data Inputs**: `a_i[31:0]`, `b_i[31:0]`, `opcode_i[3:0]`
- **Output Interface**: Ready/valid handshaking with `valid_o`, `ready_i`
- **Data Output**: `result_o[31:0]`

### Supported Operations
| Opcode | Operation | Description |
|--------|-----------|-------------|
| `0000` | ADD | Addition (a + b) |
| `0001` | SUB | Subtraction (a - b) |
| `0010` | AND | Bitwise AND (a & b) |
| `0011` | OR  | Bitwise OR (a \| b) |
| `0100` | XOR | Bitwise XOR (a ^ b) |
| `0101` | SHL | Shift left (a << b) |
| `0110` | SHR | Shift right (a >> b) |
| `0111` | MUL | Multiplication (a * b) |
| `1000` | DIV | Division (a / b) |

### Protocol
The ALU uses a ready/valid handshaking protocol:
1. When `ready_o` is high, the ALU can accept new inputs
2. When `valid_i` is asserted along with `ready_o`, inputs are captured
3. Results are available in the next cycle with `valid_o` asserted
4. When downstream asserts `ready_i` with `valid_o`, the transaction completes

## Verification Environment

The testbench is built using **PyUVM** (Python UVM) and includes:

### Test Structure
- **Base Test** (`base_test.py`): Common test infrastructure with RNG support
- **Simple Test** (`simple_test.py`): Basic functionality verification
- **Add Test** (`add_test.py`): Focused addition operation testing
- **Sequences** (`sequences.py`): Stimulus generation sequences with random-stability

### Environment Components
- **Driver**: Drives stimulus to the ALU inputs
- **Monitor**: Observes ALU inputs and outputs
- **Scoreboard**: Checks expected vs actual results
- **Coverage**: Functional and code coverage collection

### Random-Stable Stimulus Generation

The verification environment implements a sophisticated **random-stability** mechanism that provides reproducible randomized tests:

#### Key Features:
- **Hierarchical RNG System**: Each UVM component and sequences has its own Random Number Generator (RNG), which is lazily instantiated.
- **Deterministic Seeding**: Component RNGs are seeded deterministically

#### Implementation:
- **UVMComponentMixin**: Provides RNG functionality to UVM components with deterministic seeding
- **BaseSeq**: Provides RNG functionality to UVM sequences with deterministic seeding

## Coverage Metrics
When `COVERAGE_EN=1`, code coverage (only Verilator) and functional coverage are collected and a database is stored at the end of the simulation.

## File Naming Convention

Simulation outputs follow the pattern: `<TEST>_<SEED>_<SIM>.*`

Examples:
- `simple_test_1_verilator.log` - Simulation log
- `simple_test_1_verilator_results.xml` - Test results
- `simple_test_1_verilator_code_cov.dat` - Coverage data
- `simple_test_1_verilator.fst` - Waveform file
