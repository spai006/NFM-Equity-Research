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
  uint32_t count; // 4 bytes

  Record records[500]; // 500*84 = 42000 bytes
                       // total size = 42004 bytes
};

#pragma pack(pop)