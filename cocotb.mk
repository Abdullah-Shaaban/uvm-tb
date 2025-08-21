# Keep this separate Makefile to avoid interference with the main Makefile (e.g., target names)

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

ifeq ($(SIM), verilator)
    ifeq ($(WAVES), 1)
        EXTRA_ARGS += --trace --trace-fst --trace-structs
        PLUSARGS += --trace --trace-file $(OUT_NAME_PREFIX)_waves.fst
    endif
    ifeq ($(COVERAGE_EN),1)
        # Enable code coverage only. NOTE: The `--coverage` option enables SV's functional coverage as well, but we collect
        # functional coverage in Python using PyVSC.
        # TODO: how to NOT dump code coverage when test fails?!
        EXTRA_ARGS += --coverage-line --coverage-toggle --coverage-underscore
        PLUSARGS +=  +verilator+coverage+file+$(OUT_NAME_PREFIX)_code_cov.dat
    endif
    # Verilator needs to recompile if the COVERAGE_EN option is changed
    CUSTOM_COMPILE_DEPS += VAR_CACHE_COVERAGE_EN
endif

# Both Icarus and Verilator need to recompile if the WAVES option is changed
CUSTOM_COMPILE_DEPS += VAR_CACHE_WAVES

# Build directory: sim_build_<SIM>_<"cov"/"">
SIM_BUILD = sim_build_$(SIM)$(if $(filter 1,$(COVERAGE_EN)),_cov,)

include $(shell cocotb-config --makefiles)/Makefile.sim