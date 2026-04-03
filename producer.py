import mmap
import os
import ctypes # for defining the structure of the shared memory
import time
import sys
from pathlib import Path

# Connect to src modules
sys.path.append(str(Path(__file__).resolve().parent))
from src.data_ingestion.universe import Universe
import json
import yfinance as yf

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

        # Load the daily fundamental cache from disk into fast RAM
        cache_path = Path(__file__).resolve().parent / "data" / "fundamentals_cache.json"
        print(f"\nLoading fundamental cache from {cache_path}...")
        try:
            with open(cache_path, "r") as f:
                cache_dict = json.load(f)
            print("✅ Cache loaded successfully!")
        except Exception as e:
            print(f"❌ Failed to load cache: {e}. Did you run daily_fundamental_cacher.py first?")
            sys.exit(1)

        print("🚀 Starting ultra-fast IPC stream...press ctrl+c to stop\n")

        try:
            while True:
                # 1. ⚡ THE LIVE PULL: Bulk download 50 stocks simultaneously to save API delay
                print("\nFetching Live Intraday Market Snapshots...")
                yf_tickers = [t + ".NS" for t in company_tickers]
                
                import logging
                logging.getLogger('yfinance').setLevel(logging.CRITICAL)
                live_data = yf.download(yf_tickers, period="1d", interval="1m", progress=False)

                # Iterate precisely through the tickers
                for ticker in company_tickers:
                    # Wait for space in ring buffer
                    while((block.head - block.tail) % (2**32) >= 1024):
                        time.sleep(0.001) # wait for 1 ms for C++ to read from the ring buffer
                    
                    yf_ticker = ticker + ".NS"
                    
                    # Safely extract Live Price/Volume (or fallback if pre-market)
                    try:
                        if not live_data.empty:
                            live_price = float(live_data['Close'][yf_ticker].dropna().iloc[-1])
                            live_volume = float(live_data['Volume'][yf_ticker].dropna().iloc[-1])
                        else:
                            live_price, live_volume = 0.0, 0.0
                    except:
                        live_price, live_volume = 0.0, 0.0
                    
                    # Read pre-computed factors directly from fast RAM cache
                    try:
                        cal_facts = cache_dict.get(ticker, [0.0] * 10)
                        
                        # write data
                        idx = block.head % 1024
                        block.records[idx].stock_id = universe.get_id(ticker)
                        
                        # 🧬 THE HYBRID PAYLOAD: The ultimate mix of Live + Fundamental
                        block.records[idx].factors[0] = live_price
                        block.records[idx].factors[1] = live_volume / 1000.0  # Scaled volume
                        block.records[idx].factors[2] = cal_facts[0]          # PE Ratio
                        block.records[idx].factors[3] = cal_facts[1]          # PEG Ratio
                        block.records[idx].factors[4] = cal_facts[2]          # Revenue Growth
                        block.records[idx].factors[5] = cal_facts[4]          # EPS Growth
                        block.records[idx].factors[6] = cal_facts[5]          # ROE
                        block.records[idx].factors[7] = cal_facts[6]          # ROCE
                        block.records[idx].factors[8] = cal_facts[7]          # FCF/NP
                        block.records[idx].factors[9] = cal_facts[9]          # Debt/Equity

                        # atomically publish to the consumer by incrementing head
                        block.head = (block.head + 1) % (2**32)

                    except Exception as e:
                        print(f"Failed pulling variables for {ticker}: {e}")

                # API Safety Delay (Mid-Frequency tick rate)
                time.sleep(5.0)

        except KeyboardInterrupt:
            print("\nProducer stopped by user.")    
        
        del block 
        mm.close()
        os.remove(filename)

if __name__ == "__main__":
    main()
