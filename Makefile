##################
# Directories
##################
ROOT_DIR := $(abspath .)
SIM_DIR := $(ROOT_DIR)/sim
COCOTB_MAKEFILE := $(ROOT_DIR)/cocotb.mk
# Create sim directory if it doesn't exist
$(shell mkdir -p $(SIM_DIR))


#######################
# Variable Definitions
#######################
# NOTES about setting the MODULE variable:
# - The module is the Python file where CocoTB looks for tests (i.e., functions decorated with `@cocotb.test`).
# - We're using PyUVM, and we write test *classes* decorated with `@pyuvm.test()`, which creates a cocotb test under the hood.
# - CocoTB will start searching for the module at `/tb`. So, we tell CocoTB to look for
#   the "package" `tests` and inside that, look for the "module" `my_test`.
TEST ?= simple_test
MODULE := tests.$(TEST)
SEED ?= 1
LOG_LEVEL ?= INFO
SIM ?= verilator
WAVES ?= 0
# NOTE: cocotb looks for an env variable called COVERAGE -> we use a different name
COVERAGE_EN ?= 0
# NOTES on PYTHONPATH:
# - Python uses PYTHONPATH to find modules when `import`ing
# - Here, we set PYTHONPATH to the "root" directory of the all verification files (`~/sv-cocotb-project/tb`).
# - This allows Python to find packages starting from `~/sv-cocotb-project/tb`.
# - We don't need an `__init__.py` file in the `tb` directory itself (having one won't hurt).
# - However, we do need an `__init__.py` file in the `tests` and `env` directories to make them packages,
#   so Python (i.e., CocoTB) can import them or import modules from them.
export PYTHONPATH := $(ROOT_DIR)/tb
TOPLEVEL_LANG := verilog
VERILOG_SOURCES := $(wildcard $(ROOT_DIR)/rtl/*.sv)
TOPLEVEL := alu
# Convention for logs/waves naming
export OUT_NAME_PREFIX := $(TEST)_$(SEED)_$(SIM)

#######################
# Targets Definitions
#######################

# Single test target
.PHONY: sim
sim:
	@echo "Running test: $(TEST) (output: sim/$(OUT_NAME_PREFIX).log)"
	$(MAKE) sim -C $(SIM_DIR) -f $(COCOTB_MAKEFILE) TOPLEVEL_LANG=$(TOPLEVEL_LANG) \
	VERILOG_SOURCES="$(VERILOG_SOURCES)" TOPLEVEL=$(TOPLEVEL) MODULE=$(MODULE) SIM=$(SIM) \
	RANDOM_SEED=$(SEED) COCOTB_LOG_LEVEL=$(LOG_LEVEL) COCOTB_RESULTS_FILE=$(OUT_NAME_PREFIX)_results.xml \
	WAVES=$(WAVES) > sim/$(OUT_NAME_PREFIX).log 2>&1
	@if [ "$(COVERAGE_EN)" = "1" ]; then \
		if [ -f $$(find $(SIM_DIR) -name "$(OUT_NAME_PREFIX)_code_cov.dat") ]; then \
			cd $(SIM_DIR); \
			verilator_coverage $(OUT_NAME_PREFIX)_code_cov.dat --write-info $(OUT_NAME_PREFIX)_code_cov.info; \
			genhtml $(OUT_NAME_PREFIX)_code_cov.info --legend --show-details --branch-coverage --output-directory $(OUT_NAME_PREFIX)_code_cov_html > /dev/null; \
		else \
			echo "No code_cov.dat file found"; \
		fi; \
	fi

# Regression target
REGRESSION ?= regression
TESTS := $(shell grep -v '^#' $(ROOT_DIR)/tb/tests/$(REGRESSION).txt | tr '\n' ' ')
.PHONY: regression $(TESTS)
$(TESTS):
	$(MAKE) sim TEST=$@
regression: $(TESTS)
	@echo "All regression tests completed"

# Target to view waveforms. NOTE: only verilator dumps waves until now
view_waves:
	@echo "Viewing waveforms for: $(TEST) with seed $(SEED)"
	@wave_file=$$(find sim -name "$(TEST)_$(SEED)*.fst"); \
	if [ -f "$$wave_file" ]; then \
		gtkwave "$$wave_file" & \
	else \
		echo "No waveform file found."; \
	fi

# Clean target: removes the simulation directory and Python cache folders
PY_CACHES := $(shell find $(ROOT_DIR)/tb -type d -name '__pycache__')
.PHONY: clean
clean:
	rm -rf $(SIM_DIR)
	rm -rf $(PY_CACHES)

.PHONY: help
help:
	@echo "Makefile for running cocotb tests"
	@echo "Usage:"
	@echo "  make sim     - Run the simulation"
	@echo "  make clean   - Clean the simulation directory"
	@echo "  make help    - Show this help message"
	@echo ""
	@echo "Environment Variables:"
	@echo "  SIM          - Simulation tool (default: icarus)"
	@echo "  TEST         - Python module containing PyUVM tests (default: simple_test)"
	@echo "  SEED         - Random seed for the simulation (default: 1)"
	@echo "  LOG_LEVEL    - Log level for the simulation (default: INFO)"
	@echo "  WAVES        - Enable waveform dumping (default: 0)"

# Mechanism to turn a variable into a prerequisite -> create a file that caches the variable value.
py:
VAR_CACHE_%: py
	@if [ ! -f $@ ]; then \
		echo "$($*)" > $@; \
		echo "Variable $* cached in $@"; \
	elif [ "$($*)" != "$$(cat $@)" ]; then \
		echo "$($*)" > $@; \
		echo "Variable $* updated in $@"; \
	else \
		echo "Variable $* value not changed"; \
	fi

# Target to merge results and display Verification Dashboard
verif_dashboard:
	python3 verif_dashboard.py --sim-dir $(SIM_DIR)
