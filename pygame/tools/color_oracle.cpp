// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only exhaustive original 16-bit RGB conversion output.
#include "rich4/graphics.hpp"
#include <fstream>

int main(int argc,char **argv){
    if(argc!=2)return 2;
    auto image=rich4::graphics::make_canvas(256,256);
    for(unsigned i=0;i<65536;++i)image.pixels[i]=static_cast<std::uint16_t>(i);
    const auto colors=rich4::graphics::to_argb8888(image);
    std::ofstream out(argv[1],std::ios::binary);
    for(auto p:colors){out.put(static_cast<char>((p>>16)&255));out.put(static_cast<char>((p>>8)&255));out.put(static_cast<char>(p&255));out.put(static_cast<char>(p>>24));}
    return out?0:1;
}
