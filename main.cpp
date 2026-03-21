// open market_state.bin using platform specific memory mapping
#include "shared_memory.h"
#include <algorithm>
#include <fstream>
#include <iostream>
#include <sstream>
#include <unordered_map>
#include <vector>
#include <chrono>

#ifdef _WIN32
#include <windows.h>
#else
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#endif

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

  // Load Ticker Map to translate C++ integers back to human names
  auto ticker_map = load_universe("data/universe_master.csv");

  // Opening the exact file Python creates
#ifdef _WIN32
  HANDLE hFile = CreateFileA("market_state.bin", GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
  if (hFile != INVALID_HANDLE_VALUE) {
    LARGE_INTEGER fileSize;
    if (GetFileSizeEx(hFile, &fileSize)) {
      HANDLE hMap = CreateFileMappingA(hFile, NULL, PAGE_READONLY, 0, 0, NULL);
      if (hMap != NULL) {
        void* addr = MapViewOfFile(hMap, FILE_MAP_READ, 0, 0, 0);
        if (addr != NULL) {
          SharedBlock *block = static_cast<SharedBlock *>(addr);
          std::cout << "Consumer: Successfully mapped " << fileSize.QuadPart << " bytes.\n";
#else
  int fd = open("market_state.bin", O_RDONLY);
  if (fd != -1) {
    struct stat sb;
    if (fstat(fd, &sb) != -1) {
      void *addr = mmap(NULL, sb.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
      if (addr != MAP_FAILED) {
        SharedBlock *block = static_cast<SharedBlock *>(addr);
        std::cout << "Consumer: Successfully mapped " << sb.st_size << " bytes.\n";
#endif
        std::cout << "Consumer: Found " << block->count << " records."
                  << std::endl;

        // 2. Define custom weights for scoring our NFM (Negative for P/E, PEG, and D/E)
        double weights[10] = {-0.15, -0.15, 0.10, 0.10, 0.15,
                              0.10, 0.10, 0.05, 0.05, -0.05};

        // Structure to store pair of stock_id, final score, and attribution
        // breakdown.
        // NOTE: Tracking `contributions` inside the struct ensures that when we
        // run the O(N log N) sorting algorithm below, the attribution data
        // travels securely alongside the stock ID without getting decoupled.
        struct ScoredStock {
          int32_t stock_id;
          double score;
          double contributions[10];
        };

        std::vector<ScoredStock> vector_scores;
        vector_scores.reserve(block->count);

        // 3. Compute full score vector and capture attribution logic
        for (uint32_t i = 0; i < block->count; ++i) {
          double total_score = 0.0;
          double contribs[10] = {0.0};

          // Iterate over all 10 factors to calculate their weighted
          // contributions
          for (int j = 0; j < 10; ++j) {

            // MATH: contribution_j = factor_j * weight_j
            double c = block->records[i].factors[j] * weights[j];

            contribs[j] = c;  // Record the isolated contribution of factor 'j'
            total_score += c; // Accumulate it into the master score
          }

          ScoredStock st;
          st.stock_id = block->records[i].stock_id;
          st.score = total_score;

          // Copy the local computed contributions into our persistent tracking
          // struct
          for (int j = 0; j < 10; ++j) {
            st.contributions[j] = contribs[j];
          }
          vector_scores.push_back(st);
        }

        // 4. Sort descending using a lambda
        std::sort(vector_scores.begin(), vector_scores.end(),
                  [](const ScoredStock &a, const ScoredStock &b) {
                    return a.score > b.score;
                  });

        // 5. Print top-10 ranked stocks with Human Readable Tickers
        std::cout << "\n--- TOP 10 NFM RANKED STOCKS ---" << std::endl;
        for (int i = 0; i < std::min(10, (int)vector_scores.size()); ++i) {
          std::string ticker = "UNKNOWN";
          if (ticker_map.find(vector_scores[i].stock_id) != ticker_map.end()) {
            ticker = ticker_map[vector_scores[i].stock_id];
          }
          std::cout << "Rank " << (i + 1) << ": " << ticker << " (ID "
                    << vector_scores[i].stock_id
                    << ") | Score: " << vector_scores[i].score << std::endl;
        }

        // 6. Write top 50 to reports/top50.csv
        std::ofstream outfile("reports/top50.csv");
        if (outfile.is_open()) {
          outfile << "rank,ticker,score,pe_contrib,peg_contrib,"
                     "rev_1y_contrib,rev_10y_contrib,eps_grow_contrib,"
                     "roe_contrib,roce_contrib,fcf_np_contrib,fcf_rev_contrib,de_contrib\n";
          for (int i = 0; i < std::min(50, (int)vector_scores.size()); ++i) {
            std::string ticker = "UNKNOWN";
            if (ticker_map.find(vector_scores[i].stock_id) !=
                ticker_map.end()) {
              ticker = ticker_map[vector_scores[i].stock_id];
            }
            outfile << (i + 1) << "," << ticker << "," << vector_scores[i].score
                    << "," << vector_scores[i].contributions[0] << ","
                    << vector_scores[i].contributions[1] << ","
                    << vector_scores[i].contributions[2] << ","
                    << vector_scores[i].contributions[3] << ","
                    << vector_scores[i].contributions[4] << ","
                    << vector_scores[i].contributions[5] << ","
                    << vector_scores[i].contributions[6] << ","
                    << vector_scores[i].contributions[7] << ","
                    << vector_scores[i].contributions[8] << ","
                    << vector_scores[i].contributions[9] << "\n";
          }
          outfile.close();
          std::cout << "\nSUCCESS: Exported top 50 ranked stocks to "
                       "reports/top50.csv!"
                    << std::endl;
        } else {
          std::cerr << "Failed to open reports/top50.csv for writing. Does the "
                       "directory exist?"
                    << std::endl;
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
