// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only raw pixels stay in a temporary directory and are never published.
#include "rich4/terrain.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>

void u32(std::ostream &out, std::uint32_t n) {for (unsigned i=0;i<4;++i) out.put(static_cast<char>((n>>(i*8))&255));}
void u16(std::ostream &out, std::uint16_t n) {out.put(static_cast<char>(n&255));out.put(static_cast<char>(n>>8));}
void pixels(std::ostream &out, const rich4::graphics::Image &image, unsigned status=0) {
    u32(out,status);u32(out,image.pixels.size());u32(out,image.opaque_pixels.size());
    for (auto p:image.pixels) {out.put(static_cast<char>(p&255));out.put(static_cast<char>(p>>8));}
    for (auto p:image.opaque_pixels) out.put(static_cast<char>(p));
    if(!out)throw std::runtime_error("output failed");
}
int main(int argc,char **argv){
    try {
        if(argc==4&&std::string(argv[1])=="--ground") {
            std::ifstream input(argv[2],std::ios::binary);
            if(!input)throw std::runtime_error("missing ground input");
            std::vector<std::uint8_t> data{std::istreambuf_iterator<char>(input),{}};
            auto ground=rich4::terrain::parse_ground(data);
            std::cout<<ground.width_tiles<<' '<<ground.height_tiles<<' '<<ground.reserved<<' '<<ground.tile_count()<<'\n';
            auto image=rich4::terrain::render_overview(ground);
            std::ofstream output(argv[3],std::ios::binary);
            u32(output,ground.tile_indices.size());u32(output,ground.tile_bytes.size());
            for(auto n:ground.palette)u16(output,n);
            for(auto n:ground.tile_indices)u16(output,n);
            output.write(reinterpret_cast<const char*>(ground.tile_bytes.data()),static_cast<std::streamsize>(ground.tile_bytes.size()));
            pixels(output,image);return 0;
        }
        if(argc!=3||std::string(argv[1])!="--quads")return 2;
        std::array<std::uint8_t,1024> texture;
        std::array<std::uint16_t,256> palette;
        for(unsigned i=0;i<256;++i)palette[i]=static_cast<std::uint16_t>((i*0x123+0x11)&0x7fff);
        for(unsigned y=0;y<32;++y)for(unsigned x=0;x<32;++x)texture[y*32+x]=static_cast<std::uint8_t>(x+y*7);
        std::ofstream output(argv[2],std::ios::binary);
        unsigned mask,count=0;
        while(std::cin>>mask){
            rich4::graphics::Rect clip;std::cin>>clip.left>>clip.top>>clip.right>>clip.bottom;
            rich4::terrain::Quad quad;
            for(auto &p:quad){int y,x;std::cin>>y>>x;p={static_cast<std::int16_t>(y),static_cast<std::int16_t>(x)};}
            if(!std::cin)return 3;
            auto image=rich4::graphics::make_canvas(64,48,0x7bde);
            if(mask){image.opaque_pixels.resize(64*48);for(std::size_t i=0;i<image.opaque_pixels.size();++i)image.opaque_pixels[i]=i%3==0;}
            unsigned status=0;
            try{rich4::terrain::draw_tile(image,texture,palette,quad,clip);}
            catch(const std::invalid_argument&){status=1;}
            pixels(output,image,status);++count;
        }
        std::cout<<count<<'\n';
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
