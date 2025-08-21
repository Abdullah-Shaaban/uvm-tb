from enum import IntEnum
from random import Random
from cocotb.triggers import RisingEdge

class AluOp(IntEnum):
    """ ALU operation codes """	
    ADD = 0b0000  # Addition
    SUB = 0b0001  # Subtraction  
    AND = 0b0010  # Bitwise AND
    OR  = 0b0011  # Bitwise OR
    XOR = 0b0100  # Bitwise XOR
    SL = 0b0101  # Shift left
    SR = 0b0110  # Shift right
    MUL = 0b0111  # Multiplication
    DIV = 0b1000  # Division

async def wait_for_ready_valid(dut, ready_sig, valid_sig):
        await RisingEdge(dut.clk_i)
        while not (int(valid_sig.value) and int(ready_sig.value)):
            await RisingEdge(dut.clk_i)

class UVMComponentMixin:
    """
    Mixin class to add a random number generator (RNG) to UVM components.
    For random-stability (reproducible tests), the RNG's seed is created
    upon constructing the component. Because component creation is
    deterministic (UVM style), the RNG will always be seeded with the same value.
    """
    seeding_rng = Random()
    def __init__(self):
        self._rng = None
        self._seed = self.seeding_rng.randint(0, 2**32 - 1)

    @property
    def rng(self):
        """
        Return the random number generator (RNG) for this component.
        If the RNG is not initialized, it will be created."""
        if self._rng is None:
            self._rng = Random(self._seed)
        return self._rng