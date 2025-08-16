from libc.stdint cimport uint32_t
from libc.stdlib cimport malloc, free
from libcpp.atomic cimport atomic
from cpython.ref cimport Py_INCREF, Py_DECREF


cdef extern from "<atomic>" namespace "std":
    cdef enum memory_order:
        memory_order_relaxed
        memory_order_acquire
        memory_order_release
        memory_order_seq_cst

cdef class SPMCReader:
    cdef SPMCQueue queue
    cdef uint32_t next_idx

    def __cinit__(self, SPMCQueue queue, uint32_t start_idx):
        self.queue = queue
        self.next_idx = start_idx

    cpdef read(self):
        """Read next message from queue, returns None if no data available"""
        cdef uint32_t blk_idx = self.next_idx % self.queue.CNT
        cdef uint32_t new_idx = self.queue._get_block_idx(blk_idx)

        if <int> (new_idx - self.next_idx) < 0:
            return None

        self.next_idx = new_idx + 1
        return self.queue._get_block_data(blk_idx)

    cpdef read_last(self):
        """Read all available messages and return the last one"""
        ret = None
        while True:
            cur = self.read()
            if cur is None:
                break
            ret = cur
        return ret

cdef struct Block:
    uint32_t idx
    void * data_ptr

cdef class SPMCQueue:
    cdef readonly uint32_t CNT
    cdef Block * blks
    cdef uint32_t write_idx

    def __cinit__(self, uint32_t size=512):
        # Ensure size is power of 2
        if size == 0 or (size & (size - 1)) != 0:
            raise ValueError("Size must be a power of 2")

        self.CNT = size
        self.blks = <Block *> malloc(size * sizeof(Block))
        if self.blks == NULL:
            raise MemoryError("Failed to allocate memory for queue")

        # Initialize blocks
        cdef uint32_t i
        for i in range(size):
            self.blks[i].idx = 0
            self.blks[i].data_ptr = NULL

        self.write_idx = 0

    def __dealloc__(self):
        cdef uint32_t i
        if self.blks != NULL:
            # Decrease ref count for stored Python objects
            for i in range(self.CNT):
                if self.blks[i].data_ptr != NULL:
                    Py_DECREF(<object> self.blks[i].data_ptr)
            free(self.blks)

    cpdef get_reader(self):
        """Create a new reader starting from the current write position"""
        cdef uint32_t start_idx = self.write_idx + 1
        return SPMCReader(self, start_idx)

    cpdef write(self, data):
        """Write data to the queue. Data can be any Python object."""
        self.write_idx += 1
        cdef uint32_t current_write_idx = self.write_idx
        cdef uint32_t blk_idx = current_write_idx % self.CNT
        cdef Block * blk = &self.blks[blk_idx]

        # Decrease ref count of old data if exists
        if blk.data_ptr != NULL:
            Py_DECREF(<object> blk.data_ptr)

        # Store reference to new data (increase ref count)
        Py_INCREF(data)
        blk.data_ptr = <void *> data

        # Atomic release - cast to atomic and store (like C++ version)
        (<atomic[uint32_t] *> &blk.idx).store(current_write_idx, memory_order_release)

    cdef inline uint32_t _get_block_idx(self, uint32_t blk_idx):
        """Internal method to get block index"""
        return (<atomic[uint32_t] *> &self.blks[blk_idx].idx).load(memory_order_acquire)

    cdef inline object _get_block_data(self, uint32_t blk_idx):
        """Internal method to get block data"""
        cdef Block * blk = &self.blks[blk_idx]
        if blk.data_ptr == NULL:
            return None

        # Return the stored Python object directly
        return <object> blk.data_ptr