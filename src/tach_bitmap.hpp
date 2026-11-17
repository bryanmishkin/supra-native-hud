#ifndef SUPRA_TACH_BITMAP_HPP
#define SUPRA_TACH_BITMAP_HPP
#include "hud_core.hpp"
#include <vector>
namespace supra {
// Exact live-negotiated bitmap geometry. Opaque BGRA, ready for RLE32.
std::vector<unsigned char> tachBitmap(const Frame& frame);
// Optional S2000-inspired layout; color projection requires vehicle validation.
std::vector<unsigned char> tachBitmapSport(const Frame& frame);
// V2 offline candidate in the existing 150x36 canvas. No live source selection.
// Unavailable boost is rendered as dashes, never as a synthetic live value.
std::vector<unsigned char> tachBitmapV2(const Frame& frame);
}
#endif
