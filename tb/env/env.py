from enum import Enum
import os
from random import Random
from pyuvm import uvm_sequencer, uvm_driver, uvm_monitor, uvm_subscriber, uvm_analysis_port, uvm_sequence_item, uvm_agent, uvm_env, ConfigDB
import cocotb
from cocotb.triggers import FallingEdge, Event
from cocotb.clock import Clock
import vsc
from env.utils import AluOp, wait_for_ready_valid

class AluEnv(uvm_env):
    def build_phase(self):
        self.agent = AluAgent("agent", self)
        self.scoreboard = AluScoreboard("scoreboard", self)
    def connect_phase(self):
        self.agent.monitor.ap.connect(self.scoreboard.analysis_export)
    async def run_phase(self):
        self.logger.info("Starting clock")
        cocotb.start_soon(Clock(cocotb.top.clk_i, 1, units="ns").start())


class AluAgent(uvm_agent):
    def build_phase(self):
        self.seqr = uvm_sequencer("seqr", self)
        self.driver = AluDriver("driver", self)
        self.monitor = AluMonitor("monitor", self)
    def connect_phase(self):
        self.driver.seq_item_port.connect(self.seqr.seq_item_export)

class AluDriver(uvm_driver):

    async def run_phase(self):
        dut = cocotb.top
        dut.valid_i.value = 0 # Input is not valid by default
        # Wait for the first reset to finish
        reset_event = ConfigDB().get(None, "", "reset_finished_event")
        await reset_event.wait()
        dut.ready_i.value = 1 # TB is always ready to accept DUT's output
        while True:
            item: AluTxn = await self.seq_item_port.get_next_item()
            await FallingEdge(dut.clk_i)
            dut.valid_i.value = 1
            dut.opcode_i.value = item.opcode.value
            dut.a_i.value = item.a
            dut.b_i.value = item.b
            await wait_for_ready_valid(dut, dut.ready_o, dut.valid_i)
            self.seq_item_port.item_done()
            self.logger.info(f"Applied item: {item}")


class AluMonitor(uvm_monitor):
    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)
        self.dut = cocotb.top
        if os.getenv("COVERAGE_EN") == "1":
            self.cov_group = AluCovGroup()
            self.collect_coverage = True
        else:
            self.collect_coverage = False

    async def run_phase(self):
        dut = cocotb.top
        # Wait for the first reset to finish
        reset_event = ConfigDB().get(None, "", "reset_finished_event")
        await reset_event.wait()
        while True:
            # Wait for input to be accepted by the DUT
            await wait_for_ready_valid(dut, dut.ready_o, dut.valid_i)
            item = AluTxn("item")
            item.opcode = AluOp(int(dut.opcode_i))
            item.a = int(dut.a_i)
            item.b = int(dut.b_i)
            
            # Wait for the DUT result to be ready
            await wait_for_ready_valid(dut, dut.ready_i, dut.valid_o)
            item.result = int(dut.result_o)
            self.logger.info(f"Observed item: {item}")
            self.ap.write(item)
            if self.collect_coverage:
                self.cov_group.alu_txn = item
                self.cov_group.sample()

    def report_phase(self):
        super().report_phase()
        if self.collect_coverage:
            prefix = os.getenv("OUT_NAME_PREFIX", "")
            # Coverage report
            with open(f"{prefix}_func_cov.log", "w") as fp:
                vsc.report_coverage(fp=fp, details=True)
            # Coverage DB
            with open(f"{prefix}_func_cov.xml", "w") as fp:
                vsc.write_coverage_db(filename=fp)

class AluScoreboard(uvm_subscriber):
    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.compare_event = Event()
        self.item = None

    def write(self, item):
        self.item = item
        self.compare_event.set()
        self.logger.info(f"Received item: {item}")

    async def run_phase(self):
        while True:
            await self.compare_event.wait()
            item: AluTxn = self.item
            # Generate the expected result
            expected_result = None
            result_mask = (1 << 32) - 1  # Mask for 32-bit result
            match item.opcode:
                case AluOp.ADD:
                    expected_result = item.a + item.b
                case AluOp.SUB:
                    expected_result = item.a - item.b
                case AluOp.AND:
                    expected_result = item.a & item.b
                case AluOp.OR:
                    expected_result = item.a | item.b
                case AluOp.XOR:
                    expected_result = item.a ^ item.b
                case AluOp.SL:
                    expected_result = item.a << item.b
                case AluOp.SR:
                    expected_result = item.a >> item.b   
                case AluOp.MUL:
                    expected_result = item.a * item.b
                case AluOp.DIV:
                    expected_result = item.a // item.b
            expected_result &= result_mask
            if item.result != expected_result:
                self.logger.error(f"Opcode {item.opcode.name} failed. Expected {expected_result}, got {item.result}")
                assert False 
            else: 
                self.logger.info(f"Opcode {item.opcode.name} passed. Input: {item.a}, {item.b}, Output: {item.result}")
            self.compare_event.clear()


class AluTxn(uvm_sequence_item):
    operand_bitwidth = 8  # Number of bits for inputs a and b, default is 8 bits

    def __init__(self, name, parent = None, a: int = 0, b: int = 0, opcode: AluOp = AluOp.ADD):
        super().__init__(name)
        self.opcode: AluOp = opcode
        self.a = a
        self.b = b
        self.result = None
        self.parent = parent

    def randomize(self):
        """Randomize the item"""
        rng: Random = self.parent.rng
        assert isinstance(rng, Random), "Couldn't find RNG of parent sequence/test/component"
        self.opcode = rng.choice(list(AluOp))
        self.rnd_operands()

    def rnd_operands(self):
        """Randomize the operands a and b"""
        rng: Random = self.parent.rng
        assert isinstance(rng, Random), "Couldn't find RNG of parent sequence/test/component"
        self.a = rng.randint(0, 2**self.operand_bitwidth - 1)
        self.b = rng.randint(0, 2**self.operand_bitwidth - 1)
        self.post_randomize()

    def post_randomize(self):
        """Post-randomization processing"""
        # Can't divide by zero
        if self.opcode is AluOp.DIV and self.b == 0:
            self.b = 1

    def __eq__(self, item) -> bool:
        return self.opcode is item.opcode and self.a == item.a and self.b == item.b and self.result == item.result

    def __repr__(self):
        return f"opcode: {self.opcode.name}, a: {self.a}, b: {self.b}, result: {self.result}"

@vsc.covergroup
class AluCovGroup():

    class OperandsEnum(Enum):
        POSITIVE = 0
        NEGATIVE = 1
        ZERO = 2

    def operand_enum(self, value: int) -> OperandsEnum:
        if value > 0:
            return self.OperandsEnum.POSITIVE.value
        elif value < 0:
            return self.OperandsEnum.NEGATIVE.value
        else:
            return self.OperandsEnum.ZERO.value

    def __init__(self):

        self.alu_txn: AluTxn = None

        # Opcode coverpoint
        self.opcode_cp = vsc.coverpoint(
            name="opcode",
            target=lambda: self.alu_txn.opcode.value,
            bins={op.name: vsc.bin(op.value) for op in AluOp})

        # Operand A coverpoint
        self.a_cp = vsc.coverpoint(
            name="operand_a",
            target=lambda: self.operand_enum(self.alu_txn.a),
            bins={"positive": vsc.bin(self.OperandsEnum.POSITIVE.value),
                  "negative": vsc.bin(self.OperandsEnum.NEGATIVE.value),
                  "zero": vsc.bin(self.OperandsEnum.ZERO.value)})


        # Operand B coverpoint
        self.b_cp = vsc.coverpoint(
            name="operand_b",
            target=lambda: self.operand_enum(self.alu_txn.b),
            bins={"positive": vsc.bin(self.OperandsEnum.POSITIVE.value),
                  "negative": vsc.bin(self.OperandsEnum.NEGATIVE.value),
                  "zero": vsc.bin(self.OperandsEnum.ZERO.value)})

        # Cross. TODO: ignore bins with opcode==DIV and b==0
        self.opcode_operands_cross = vsc.cross(
            name="opcode_operands_cross",
            target_l=[self.opcode_cp, self.a_cp, self.b_cp])

        # TODO: collect coverage for the result: zero, positive, negative, with-carry, overflow
