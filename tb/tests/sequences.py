from random import Random
import cocotb
from pyuvm import uvm_sequence
from env.env import AluTxn
from env.utils import AluOp

class BaseSeq(uvm_sequence):
    """
    Base class for all sequences. It introduces a random number generator (RNG).
    For random-stability (reproducible tests), the RNG is seeded with a random
    value derived from the parent sequence or test. If the parent does not have
    a RNG, the RNG is not seeded and a warning is logged.
    """
    def __init__(self, name, parent=None):
        super().__init__(name)
        self._rng = None
        self._seed = None
        try:
            self._seed = parent.rng.random()
        except AttributeError:
            cocotb.log.warning(f"{self.get_full_name()}: Parent sequence/test does not have a RNG. Could not seed the sequence's RNG.")

    @property
    def rng(self):
        """
        Return the random number generator (RNG) for this sequence.
        If the RNG is not initialized, it will be created and seeded with the
        sequence's seed if available.
        """
        if self._rng is None:
            self._rng = Random()
            if self._seed is not None:
                self._rng.seed(self._seed)
        return self._rng

class SimpleSeq(BaseSeq):
    """Test all instructions of the ALU"""

    async def body(self):
        for _ in AluOp:
            item = AluTxn(name="item", parent=self)
            item.randomize()
            await self.start_item(item)
            await self.finish_item(item)

class AddSeq(BaseSeq):
    """Test the ADD instruction of the ALU"""

    async def body(self):
        for _ in range(5):
            item = AluTxn(name="item", parent=self, opcode=AluOp.ADD)
            item.rnd_operands()
            await self.start_item(item)
            await self.finish_item(item)