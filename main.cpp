// open market_state.bin using platform specific memory mapping
#include "shared_memory.h"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <fstream>
#include <iostream>
#include <sstream>
#include <thread>
#include <unordered_map>
#include <vector>
#ifdef _WIN32
#include <windows.h>
#else
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#endif

// we are implementing this fucnction to map each stock id to ticker name
// mainly doing this for output/ display purposes. could have directly shown the
// final scores with stock id also.
std::unordered_map<int, std::string>
load_universe(const std::string &filepath) {
  std::unordered_map<int, std::string> ticker_map;
  std::ifstream file(filepath);
  if (!file.is_open()) {
    std::cerr << "Could not open universe file." << std::endl;
    return ticker_map;
  }

  std::string line;
  // skip header
  std::getline(file, line);
  while (std::getline(file, line)) {
    std::stringstream ss(line);
    std::string id_str, ticker;
    if (std::getline(ss, id_str, ',') && std::getline(ss, ticker, ',')) {
      if (!ticker.empty() && ticker.back() == '\r') {
        ticker.pop_back();
      }
      if (!ticker.empty() && ticker.back() == '\n') {
        ticker.pop_back();
      }
      ticker_map[std::stoi(id_str)] = ticker;
    }
  }
  return ticker_map;
}

int main() {
  auto t1 = std::chrono::high_resolution_clock::now();

  // we are loading the universe file to map each stock id to ticker name
  // mainly doing this for output/ display purposes. could have directly shown
  // the final scores with stock id also.
  auto ticker_map = load_universe("data/universe_master.csv");

  // Opening the exact file Python creates
#ifdef _WIN32
  HANDLE hFile = CreateFileA("market_state.bin", GENERIC_READ | GENERIC_WRITE,
                             FILE_SHARE_READ | FILE_SHARE_WRITE, NULL,
                             OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
  if (hFile != INVALID_HANDLE_VALUE) {
    LARGE_INTEGER fileSize;
    if (GetFileSizeEx(hFile, &fileSize)) {
      HANDLE hMap = CreateFileMappingA(hFile, NULL, PAGE_READWRITE, 0, 0, NULL);
      if (hMap != NULL) {
        void *addr = MapViewOfFile(hMap, FILE_MAP_ALL_ACCESS, 0, 0, 0);
        if (addr != NULL) {
          SharedBlock *block = static_cast<SharedBlock *>(addr);
          std::cout << "Consumer: Successfully mapped " << fileSize.QuadPart
                    << " bytes.\n";
#else
  // so basically we are loading the file - market_state.bin made by python into
  // the memory of this c++ program. the file is present in the /tmp directory
  // which is a temporary file system that is mounted on RAM so it is very fast
  // to access. python writes into the file and c++ reads from it.

  int fd = open("market_state.bin", O_RDWR); // read write 
  if (fd != -1) {
    struct stat sb;
    if (fstat(fd, &sb) != -1) { // fstat checks how big the file is.
      // we are doing this to make sure that we are reading the same file that
      // python is writing to.
      void *addr =
          mmap(NULL, sb.st_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
      // mmap writes the file inRAM. it returns a generic pointer pointing to
      // the raw bytes in RAM.
      if (addr != MAP_FAILED) {
        SharedBlock *block = static_cast<SharedBlock *>(addr);
        // we are casting it to SharedBlock* to make it usable.
        std::cout << "Consumer: Successfully mapped " << sb.st_size
                  << " bytes.\n";
#endif
          std::cout << "Consumer: Listening for live data streams...\n";

          double weights[10] = {-0.15, -0.15, 0.10, 0.10, 0.15,
                                0.10,  0.10,  0.05, 0.05, -0.05};

          struct ScoredStock {
            int32_t stock_id;
            double score;
            double contributions[10];
          };
          // this is a struct that is used to store the score of each stock
          // along with the contributions by 10 of its factors.

          std::unordered_map<int32_t, ScoredStock> live_state;
          // we are creating a map to store the state of a stock
          // key = stock_id, value = ScoredStock struct
          uint32_t updates_processed = 0;

          // Initialize tail safely
          block->tail.store(0);
          // we are explicitly setting tail to 0 to ensure that we are reading
          // from the start of our ring buffer.

          // block->tail.store(0, std::memory_order_relaxed);
          // since tail is an atomic variable and we are changing the value to
          // 0. generally with atomic variables, the compiler assumes that you
          // want the strictest possible safety and the compiler might try to
          // optimize the code and reorder the operations. (flushing cpu cache,
          // block threads, etc) std::memory_order_relaxed tells the compiler
          // that we are not concerned about the order of operations and we are
          // only concerned about the value of the atomic variable.

          while (true) {
            uint32_t current_head = block->head.load(std::memory_order_acquire);
            // std::memory_order_acquire is a hardware level instruction that
            // tells the cpu to not reorder any operations that happen after
            // this load. this ensures that we are reading the most recent value
            // of head.
            // it forces the c++ program to synchronize its memory with whatever
            // python just wrote

            uint32_t current_tail = block->tail.load(std::memory_order_relaxed);
            // we are using relaxed memory order for tail, because only c++
            // changes the tail so we dont need any special syncing with memory
            // to read the variable.

            // Yield CPU if buffer is empty
            if (current_tail == current_head) {
              std::this_thread::sleep_for(std::chrono::milliseconds(1));
              // instead of constantly checking if the buffer is empty, we are
              // sleeping for 1ms and then checking again.
              continue;
            }

            // Drain the ring buffer until tail catches up to head
            while (current_tail != current_head) {
              int idx = current_tail % 1024;
              Record &rec = block->records[idx];

              double total_score = 0.0;
              double contribs[10] = {0.0};

              // Iterate over all 10 factors to calculate their weighted
              // contributions
              for (int j = 0; j < 10; ++j) {
                double c = rec.factors[j] * weights[j];
                contribs[j] = c;
                total_score += c;
              }

              ScoredStock st;
              st.stock_id = rec.stock_id;
              st.score = total_score;
              for (int j = 0; j < 10; ++j) {
                st.contributions[j] = contribs[j];
              }

              live_state[rec.stock_id] = st;

              current_tail++;
              block->tail.store(current_tail, std::memory_order_release);
              updates_processed++;
            }

            // Recalculate and Output Top 10 periodically
            if (updates_processed >= 500) {
              std::vector<ScoredStock> sorted_stocks;
              sorted_stocks.reserve(live_state.size());
              for (auto &pair : live_state) {
                sorted_stocks.push_back(pair.second);
              }

              std::sort(sorted_stocks.begin(), sorted_stocks.end(),
                        [](const ScoredStock &a, const ScoredStock &b) {
                          return a.score > b.score;
                        });

              std::cout << "\n--- LIVE TOP 10 (Universe size: "
                        << live_state.size() << ") ---\n";
              for (int i = 0; i < std::min(10, (int)sorted_stocks.size());
                   ++i) {
                std::string ticker = "UNKNOWN";
                if (ticker_map.find(sorted_stocks[i].stock_id) !=
                    ticker_map.end()) {
                  ticker = ticker_map[sorted_stocks[i].stock_id];
                }
                std::cout << "Rank " << (i + 1) << ": " << ticker
                          << " | Score: " << sorted_stocks[i].score << "\n";
              }
              updates_processed = 0;
            }
          }
#ifdef _WIN32
          UnmapViewOfFile(addr);
        }
        CloseHandle(hMap);
      }
    }
    CloseHandle(hFile);
  } else {
    std::cerr << "Failed to open memory mapped file. Did you run Python first?"
              << std::endl;
  }
#else
      }
    }
    close(fd);
  } else {
    std::cerr << "Failed to open memory mapped file. Did you run Python first?"
              << std::endl;
  }
#endif
  auto t2 = std::chrono::high_resolution_clock::now();

  std::cout
      << "Execution latency (microseconds): "
      << std::chrono::duration_cast<std::chrono::microseconds>(t2 - t1).count()
      << "\n";
  return 0;
}
