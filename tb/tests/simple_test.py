import pyuvm
import cocotb
from cocotb.triggers import ClockCycles
from tests.sequences import SimpleSeq
from tests.base_test import BaseTest

@pyuvm.test()
class SimpleTest(BaseTest):
    """Runs the simple sequence to test all ALU instructions."""
    async def run_scenario(self):
        seq = SimpleSeq(name="seq", parent=self)
        await seq.start(self.env.agent.seqr)
        await ClockCycles(cocotb.top.clk_i, 2)  # Wait for last item to be processed
