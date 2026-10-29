#include <windows.h>
#include <cstdint>
#include <iostream>

int main() {
    static_assert(sizeof(void*) == 8, "The baseline requires x64");
    static_assert(sizeof(double) == 8, "The kernel requires float64");
    const std::uint64_t wrapped = UINT64_MAX + std::uint64_t(2);
    if (wrapped != 1 || GetCurrentProcessId() == 0) return 2;
    std::cout << "{\"compiler_msc\":" << _MSC_FULL_VER
              << ",\"pointer_bytes\":" << sizeof(void*)
              << ",\"double_bytes\":" << sizeof(double)
              << ",\"status\":\"PASS_CPP17_WINDOWS_SDK_SMOKE\"}\n";
    return 0;
}
