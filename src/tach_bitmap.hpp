#ifndef SUPRA_TACH_BITMAP_HPP
#define SUPRA_TACH_BITMAP_HPP
#include "hud_core.hpp"
#include <vector>
namespace supra {
// Exact live-negotiated bitmap geometry. Opaque BGRA, ready for RLE32.
std::vector<unsigned char> tachBitmap(const Frame& frame);
// Optional S2000-inspired layout; color projection requires vehicle validation.
std::vector<unsigned char> tachBitmapSport(const Frame& frame);
}
#endif
