# Copyright 2025 Nathan Young
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Optional
from pioemu.instruction import (
    InInstruction,
    Instruction,
    JmpInstruction,
    OutInstruction,
    PullInstruction,
    PushInstruction,
    WaitInstruction,
    IrqInstruction
)


class InstructionDecoder:
    """
    Decodes state-machine opcodes into higher-level representations.
    """

    def __init__(self, side_set_count: int = 0):
        """
        Parameters
        ----------
        side_set_count (int): Number of bits of side-set information encoded into opcodes.
        """
        self.side_set_count = side_set_count
        self.bits_for_delay = 5 - self.side_set_count
        self.delay_cycles_mask = (1 << self.bits_for_delay) - 1

    def decode(self, opcode: int) -> Optional[Instruction]:
        """
        Decodes an opcode into an object representing the instruction and its parameters.

        Parameters:
        opcode (int): The opcode to decode.

        Returns:
        Instruction: Representation of the given opcode or None when invalid/not supported
        """

        match (opcode >> 13) & 7:
            case 0:
                decoded_instruction = self._decode_jmp(opcode)
            case 1:
                decoded_instruction = self._decode_wait(opcode)
            case 2:
                decoded_instruction = self._decode_in(opcode)
            case 3:
                decoded_instruction = self._decode_out(opcode)
            case 4 if opcode & 0x0080 == 0:
                decoded_instruction = self._decode_push(opcode)
            case 4 if opcode & 0x0080 != 0:
                decoded_instruction = self._decode_pull(opcode)
            case 6:
                decoded_instruction = self._decode_irq(opcode)

            # TODO: Add support for MOV, IRQ and SET instructions
            case _:
                decoded_instruction = None

        return decoded_instruction

    def _decode_in(self, opcode: int) -> Optional[InInstruction]:
        bit_count = opcode & 0x1F
        if bit_count == 0:
            bit_count = 32

        source = (opcode >> 5) & 7

        # Check if source has been reserved for future use
        if source in (4, 5):
            return None

        delay_cycles, side_set_value = self._extract_delay_cycles_and_side_set(opcode)

        return InInstruction(
            opcode=opcode,
            source=source,
            bit_count=bit_count,
            delay_cycles=delay_cycles,
            side_set_value=side_set_value,
        )

    def _decode_jmp(self, opcode: int) -> JmpInstruction:
        delay_cycles, side_set_value = self._extract_delay_cycles_and_side_set(opcode)

        return JmpInstruction(
            opcode=opcode,
            target_address=opcode & 0x1F,
            condition=(opcode >> 5) & 7,
            delay_cycles=delay_cycles,
            side_set_value=side_set_value,
        )

    def _decode_out(self, opcode: int) -> OutInstruction:
        bit_count = opcode & 0x1F
        if bit_count == 0:
            bit_count = 32

        delay_cycles, side_set_value = self._extract_delay_cycles_and_side_set(opcode)

        return OutInstruction(
            opcode=opcode,
            destination=(opcode >> 5) & 7,
            bit_count=bit_count,
            delay_cycles=delay_cycles,
            side_set_value=side_set_value,
        )

    def _decode_pull(self, opcode: int) -> Optional[PullInstruction]:
        delay_cycles, side_set_value = self._extract_delay_cycles_and_side_set(opcode)
        return PullInstruction(
            opcode=opcode,
            if_empty=bool(opcode & 0x0040),
            block=bool(opcode & 0x0020),
            get=(opcode & 0x0010),
            get_idxI=(opcode & 0x0008),
            get_index=(opcode & 0x0007),
            delay_cycles=delay_cycles,
            side_set_value=side_set_value,
        )

    def _decode_push(self, opcode: int) -> Optional[PushInstruction]:
        delay_cycles, side_set_value = self._extract_delay_cycles_and_side_set(opcode)
        return PushInstruction(
            opcode=opcode,
            if_full=bool(opcode & 0x0040),
            block=bool(opcode & 0x0020),
            put=(opcode & 0x0010),
            put_idxI=(opcode & 0x0008),
            put_index=(opcode & 0x0007),
            delay_cycles=delay_cycles,
            side_set_value=side_set_value,
        )

    def _decode_wait(self, opcode: int) -> Optional[WaitInstruction]:
        delay_cycles, side_set_value = self._extract_delay_cycles_and_side_set(opcode)

        return WaitInstruction(
            opcode=opcode,
            source=(opcode >> 5) & 3,
            index=opcode & 0x1F,
            polarity=bool(opcode & 0x0080),
            delay_cycles=delay_cycles,
            side_set_value=side_set_value,
        )
    
    def _decode_irq(self, opcode: int) -> Optional[IrqInstruction
    ]:
        index = opcode & 0x7
        index_mode = (opcode >> 3) & 0x3
        wait = (opcode >> 5) & 0x1
        clr = (opcode >> 6) & 0x1

        delay_cycles, side_set_value = self._extract_delay_cycles_and_side_set(opcode)

        return IrqInstruction(
            opcode=opcode,
            index=index,
            index_mode=index_mode,
            wait=wait,
            clr=clr,
            delay_cycles=delay_cycles,
            side_set_value=side_set_value,
        )

    
    def _extract_delay_cycles_and_side_set(self, opcode: int):
        delay_cycles_and_side_set = (opcode >> 8) & 0x1F
        delay_cycles = delay_cycles_and_side_set & self.delay_cycles_mask
        side_set_value = delay_cycles_and_side_set >> self.bits_for_delay

        return (delay_cycles, side_set_value)
