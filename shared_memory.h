#include <atomic>
#include <cstdint>

#pragma pack(push, 1)
// this forces the compiler to not add padding bytes, this is very
// critical for python combatibilty.
// wihtout this python writes 42004 bytes but c++ might try to read 42008 bytes
// and crash

struct Record {
  int32_t stock_id;   // 4 bytes
  double factors[10]; // 8*10 bytes = 80 bytes
                      // total size = 84 bytes
};

struct SharedBlock {
  std::atomic<uint32_t> head; // python will increment this after writing
  std::atomic<uint32_t> tail; // c++ will increment this after reading

  Record records[1024]; // 1024*84 = 86016 bytes
                        // total size = 86020 bytes
};

#pragma pack(pop)