import pyuvm
import cocotb
from cocotb.triggers import ClockCycles
from tests.sequences import AddSeq
from tests.base_test import BaseTest

@pyuvm.test()
class AddTest(BaseTest):
    """Runs the ADD sequence to test the ADD instruction of the ALU."""
    async def run_scenario(self):
        seq = AddSeq(name="seq", parent=self)
        await seq.start(self.env.agent.seqr)
        await ClockCycles(cocotb.top.clk_i, 2)
