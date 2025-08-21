from pyuvm import uvm_test, ConfigDB
import cocotb
from cocotb.triggers import FallingEdge, ClockCycles, Event
from env.env import AluEnv
from env.utils import UVMComponentMixin

class BaseTest(uvm_test, UVMComponentMixin):
    """
    Base class for all tests. It introduces a random number generator (RNG).
    For random-stability (reproducible tests), the RNG is seeded with a random
    value derived from the parent test. If the parent does not have a RNG,
    the RNG is not seeded and a warning is logged.
    """
    def __init__(self, name, parent=None):
        uvm_test.__init__(self, name, parent)
        UVMComponentMixin.__init__(self)
        
    def build_phase(self):
        self.reset_finished_event = Event()
        ConfigDB().set(None, "*", "reset_finished_event", self.reset_finished_event)
        self.env = AluEnv("env", self)

    async def run_phase(self):
        self.raise_objection()
        # Reset then start the sequence
        self.logger.info("Resetting DUT")
        await FallingEdge(cocotb.top.clk_i)
        cocotb.top.arst_n_i.value = 0
        await ClockCycles(cocotb.top.clk_i, 2, rising=False)
        cocotb.top.arst_n_i.value = 1
        await FallingEdge(cocotb.top.clk_i)
        self.reset_finished_event.set()
        self.logger.info("Starting testcase")
        await self.run_scenario()
        self.logger.info("Dropping objection")
        self.drop_objection()    

    async def run_scenario(self):
        """
        Override this method in derived classes to implement the test scenario.
        This method is called after the DUT has been reset and before the objection is dropped.
        """
        raise NotImplementedError("run_scenario must be implemented in derived classes")
