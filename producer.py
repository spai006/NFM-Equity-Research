import mmap
import os
import ctypes # for defining the structure of the shared memory
import time
import sys
from pathlib import Path

# Connect to src modules
sys.path.append(str(Path(__file__).resolve().parent))
from src.data_ingestion.universe import Universe
from src.metrics.factors.core_factors import compute_fundamental_factors

# So basically we are using ctypes.Structure to force oython to treat these variables exactly
# like raw C data types (e.g. c_int32 = 4 bytes)

# 1. We must define the ctypes struct to explicitly match the C++ layout byte-for-byte.
class Record(ctypes.Structure):
    _pack_ = 1  # Equivalent to #pragma pack(push, 1) to prevent padding.
    # by default computers try to align memory blocks to chunks of 8 or 16 bytes for efficiency 
    # adding invisible padding bytes between variables. this line forces python to squeeze
    # entire data tightly together

    _fields_ = [
        ("stock_id", ctypes.c_int32),           # 4 bytes
        ("factors", ctypes.c_double * 10)       # 8 bytes * 10 = 80 bytes
    ]

class SharedBlock(ctypes.Structure):
    _pack_ = 1  # Crucial to pack this as well
    _fields_ = [
        ("head", ctypes.c_uint32),              # 4 bytes
        ("tail", ctypes.c_uint32),              # 4 bytes
        ("records", Record * 1024)              # 1024 * 84 = 86016 bytes
    ]

def main():
    filename = "market_state.bin" 
    # this is a temporary file that will be deleted once the program is closed
    # it is used to store the shared memory
    # it is present in the /tmp directory which is a temporary file system that is mounted on RAM
    # so it is very fast
    file_size = ctypes.sizeof(SharedBlock)      # This will precisely be 42004
    
    print(f"Python SharedBlock size: {file_size} bytes")

    # 2. Touch the file and reserve the correct amount of blank bytes on disk
    with open(filename, "wb") as f:
        f.truncate(file_size)
        # before we directly map the memory, the file should be precisely the size of our struct
        # otherwise mmap will throw an error
        # so we truncate the file to the size of our struct

    # 3. Memory-map the file
    with open(filename, "r+b") as f:
        mm = mmap.mmap(f.fileno(), file_size, access=mmap.ACCESS_WRITE) 
        # f.fileno() returns the file descriptor of the file. 
        # this tells the OS to map the file into memory
        # access=mmap.ACCESS_WRITE tells the OS that we want to write to the file
        
        # mm is a python object containing raw meaningless bytes. 
        # now if we want to use the members of the object like stock_id or factors,
        # we cannot use it directly on mm
        # so we are using this .from_buffer() method which tells python to treat the raw 
        # bytes from mm as SharedBlock struct and create a python object from it
        block = SharedBlock.from_buffer(mm)

        # 5. Populate and stream real live data
        block.head = 0
        block.tail = 0

        # Load real universe data
        print("Initializing stock universe...")
        universe = Universe()
        
        # Taking top 50 strictly mapping to C++ array requirements (if needed) or iterating full universe
        company_tickers = universe.all_tickers()[:50]
        print(f"Loaded {len(company_tickers)} tickers to stream continuously...press ctrl+c to stop")

        try:
            while True:
                # Iterate precisely through the tickers
                for ticker in company_tickers:
                    # Wait for space in ring buffer
                    while((block.head - block.tail) % (2**32) >= 1024):
                        time.sleep(0.001) # wait for 1 ms
                    
                    # Fetch real live computation
                    try:
                        print(f"Fetching updates for {ticker}...")
                        calculated_factors = compute_fundamental_factors(ticker)
                        
                        # write data
                        idx = block.head % 1024
                        block.records[idx].stock_id = universe.get_id(ticker)
                        
                        for j in range(10):
                            # Safe fallback in case of None logic internally
                            val = calculated_factors[j]
                            block.records[idx].factors[j] = val if val is not None else 0.0

                        # atomically publish to the consumer by incrementing head
                        block.head = (block.head + 1) % (2**32)

                    except Exception as e:
                        print(f"Failed pulling variables for {ticker}: {e}")

                    # Respectful rate limiting so APIs don't permanently ban our IP 
                    time.sleep(2.0)

        except KeyboardInterrupt:
            print("\nProducer stopped by user.")    
        
        del block 
        mm.close()
        os.remove(filename)

if __name__ == "__main__":
    main()
