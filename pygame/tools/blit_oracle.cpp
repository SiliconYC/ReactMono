// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only synthetic clipping, masks, opaque mode and aliasing oracle.
#include "rich4/graphics.hpp"
#include <fstream>
#include <iostream>

void u32(std::ostream &o,unsigned n){for(unsigned i=0;i<4;++i)o.put(static_cast<char>((n>>(8*i))&255));}
int main(int argc,char **argv){
    if(argc!=2)return 2;
    std::ofstream out(argv[1],std::ios::binary);unsigned count=0;
    int alias,opaque,sm,dm,sw,sh,dw,dh,ox,oy,ax,ay,l,t,r,b,seed;
    while(std::cin>>alias>>opaque>>sm>>dm>>sw>>sh>>dw>>dh>>ox>>oy>>ax>>ay>>l>>t>>r>>b>>seed){
        auto source=rich4::graphics::make_canvas(sw,sh);
        auto destination=rich4::graphics::make_canvas(dw,dh);
        source.origin_x=ox;source.origin_y=oy;
        for(std::size_t i=0;i<source.pixels.size();++i)source.pixels[i]=i%5==0?0:static_cast<std::uint16_t>(i*129+seed*73);
        for(std::size_t i=0;i<destination.pixels.size();++i)destination.pixels[i]=static_cast<std::uint16_t>(i*257+seed*29);
        if(sm){source.opaque_pixels.resize(source.pixels.size());for(std::size_t i=0;i<source.pixels.size();++i)source.opaque_pixels[i]=i%3?sm:0;}
        if(dm){destination.opaque_pixels.resize(destination.pixels.size());for(std::size_t i=0;i<destination.pixels.size();++i)destination.opaque_pixels[i]=i%4?dm:0;}
        unsigned status=0;
        try{
            if(alias){destination.origin_x=ox;destination.origin_y=oy;rich4::graphics::blit(destination,destination,ax,ay,{l,t,r,b},opaque?rich4::graphics::Transparency::opaque:rich4::graphics::Transparency::source_key);}
            else rich4::graphics::blit(destination,source,ax,ay,{l,t,r,b},opaque?rich4::graphics::Transparency::opaque:rich4::graphics::Transparency::source_key);
        }catch(const std::exception&){status=1;}
        u32(out,status);u32(out,destination.pixels.size());u32(out,destination.opaque_pixels.size());
        for(auto p:destination.pixels){out.put(static_cast<char>(p&255));out.put(static_cast<char>(p>>8));}
        for(auto p:destination.opaque_pixels)out.put(static_cast<char>(p));
        ++count;
    }
    std::cout<<count<<'\n';return out?0:1;
}
