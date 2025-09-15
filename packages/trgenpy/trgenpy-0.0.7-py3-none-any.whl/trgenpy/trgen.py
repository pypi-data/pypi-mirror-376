class Trgen:
    def __init__(self, id, memory_length=5):

        """
        Initialize a Trgen instance.

        Args:
            id (int): The ID of the trigger (0-25).
            memory_length (int): The length of the trigger memory (1-64).
            default is 5, which means 2^5 = 32 instructions.

        Raises:
            TypeError: If id or memory_length is not an integer.
            ValueError: If id or memory_length is out of allowed range.
        """

        """
        Get the ID of the trigger.
        See :class:`TrgenPin` for valid IDs.
        """
        @property
        def id(self):
            return self.id
       
        if id is None or memory_length is None:
            raise ValueError("Both 'id' and 'memory_length' must be provided.")

        if not isinstance(id, int) or not isinstance(memory_length, int):
            raise TypeError("'id' and 'memory_length' must be integers.")

        if not (0 <= id <= 25):
            raise ValueError(f"ID {id} out of allowed range (0-25)")
        if not (1 <= memory_length <= 64):
            raise ValueError(f"Memory length {memory_length} out of allowed range (1-64)")

        # Set ID
        self.id = id
        
        # Set type label
        self.type = ""
        if(id < 7 and id >= 0):
            self.type = "NeuroScan"
        elif(id < 15 and id >= 8):
            self.type = "Synamps"
        elif(id == 16):
            self.type = "TMSO"
        elif(id == 17):
            self.type = "TMSI"
        elif(id < 26 and id >= 18):
            self.type = "GPIO"
        
        # set max trigger memory length (mtml)
        self._memory_length = memory_length
        self.memory = [0] * memory_length

    def __repr__(self):
        return f"<Trgen id={self.id} instructions={len(self.memory)}>"

    def set_instruction(self, index, instruction):
        """
        Example usage:

        Example:
            .. code-block:: python
                tmso = client.create_trgen(TrgenPin.TMSO)
                tmso.set_instruction(0, active_for_us(20))
                tmso.set_instruction(1, unactive_for_us(3))
                tmso.set_instruction(2, end())

        Set an instruction at a specific index in the trigger memory.
        Args:
            index (int): The index in the trigger memory to set the instruction.
            instruction (int): The instruction to set.
        Raises:
            IndexError: If the index is out of bounds.
        """

        if not (0 <= index < self._memory_length):
            raise IndexError(f"Indice {index} fuori limiti (max {self._memory_length - 1})")
        self.memory[index] = instruction