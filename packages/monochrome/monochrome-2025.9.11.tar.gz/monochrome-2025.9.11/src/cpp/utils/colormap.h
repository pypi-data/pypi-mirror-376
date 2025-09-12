#pragma once

#include <array>
#include "utils/vectors.h"

// All ColorMaps, only append to this list and copy it to the IPC schema!
enum class ColorMap : int { GRAY, HSV, BLACKBODY, VIRIDIS, PRGn, PRGn_POS, PRGn_NEG, RdBu, Tab10, Turbo, CMOCEAN_PHASE, RED, GREEN, BLUE, SOLID};
// Names of the ColorMaps for UI
inline const char *ColorMapsNames[15] = {"Gray",  "HSV",           "Black Body",    "Viridis",
                                         "PRGn",  "PRGn Positive", "PRGn Negative", "RdBu",
                                         "Tab10", "Turbo", "cmocean:phase", "Red", "Green", "Blue", "User defined"};
// Order of the ColorMaps in UI
inline const ColorMap ColorMapDisplayOrder[15] = {
    ColorMap::GRAY, ColorMap::SOLID,         ColorMap::RED,      ColorMap::GREEN,
    ColorMap::BLUE, ColorMap::BLACKBODY,     ColorMap::VIRIDIS,  ColorMap::Turbo,
    ColorMap::RdBu, ColorMap::PRGn,          ColorMap::PRGn_POS, ColorMap::PRGn_NEG,
    ColorMap::HSV,  ColorMap::CMOCEAN_PHASE, ColorMap::Tab10};

inline bool is_diff_colormap(const ColorMap &cmap) {
  return cmap == ColorMap::PRGn || cmap == ColorMap::PRGn_POS || cmap == ColorMap::PRGn_NEG ||
         cmap == ColorMap::RdBu;
}

inline bool is_solid_colormap(const ColorMap &cmap) {
  return cmap == ColorMap::SOLID || cmap == ColorMap::RED ||
         cmap == ColorMap::GREEN || cmap == ColorMap::BLUE;
}

using ColorMapArray = std::array<float, 3 * 256>;
ColorMapArray get_colormapdata(ColorMap cmap);
Vec3f get_color(ColorMap cmap);