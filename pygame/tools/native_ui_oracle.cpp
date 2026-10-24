// SPDX-License-Identifier: GPL-3.0-or-later
// Fixed native_ui.hpp directly, with external FreeType/font; no commercial assets or game backend.
#include "native_ui.hpp"
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <sstream>

static std::string unhex(const std::string &v) {
    if(v=="-")return {};std::string s;
    for(std::size_t i=0;i<v.size();i+=2)s.push_back(static_cast<char>(std::stoul(v.substr(i,2),nullptr,16)));
    return s;
}
static std::string hex(const std::string &v) {
    std::ostringstream out;for(unsigned char c:v)out<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(c);
    return out.str().empty()?"-":out.str();
}
int main(int argc,char **argv) {
    if(argc!=3)return 2;
    try {
        using namespace rich4;
        ui::Font font(argv[1]);std::filesystem::create_directories(argv[2]);
        unsigned step=0;std::string line;
        while(std::getline(std::cin,line)) {
            std::istringstream in(line);char op;in>>op;
            if(op=='C') {
                std::string encoded;in>>encoded;auto text=unhex(encoded);const auto cp=ui::codepoints(text);
                std::cout<<cp.size();for(auto v:cp)std::cout<<' '<<std::uint32_t(v);
                std::cout<<' '<<hex(ui::big5(text))<<'\n';
            }else if(op=='G') {
                unsigned ch,size,mono;in>>ch>>size>>mono;auto &g=font.glyph(ch,size,mono);
                std::cout<<g.width<<' '<<g.height<<' '<<g.left<<' '<<g.top<<' '<<g.advance<<'\n';
                std::ofstream out(std::filesystem::path(argv[2])/(std::to_string(step)+".mask"),std::ios::binary);
                out.write(reinterpret_cast<const char*>(g.mask.data()),g.mask.size());
            }else {
                graphics::Image image;image.width=384;image.height=192;image.pixels.resize(384*192);
                int size,x,y,fg,bg;std::string encoded;
                if(op=='D') {
                    int wrap,mono;in>>size>>x>>y>>wrap>>fg>>mono>>bg>>encoded;
                    for(std::size_t i=0;i<image.pixels.size();++i)image.pixels[i]=(i*1103515245ULL+bg)&65535;
                    auto text=unhex(encoded);font.draw(image,text,x,y,size,fg,wrap,mono);
                    const auto box=font.ink_bounds(text,size,0,mono);
                    std::cout<<font.measure(text,size,mono)<<' '<<box.left<<' '<<box.top<<' '<<box.right<<' '<<box.bottom<<'\n';
                }else if(op=='B') {
                    int effect,bold,shadow,outline,gap,center;
                    in>>size>>x>>y>>fg>>effect>>bold>>shadow>>outline>>gap>>center>>bg>>encoded;
                    for(std::size_t i=0;i<image.pixels.size();++i)image.pixels[i]=(i*1103515245ULL+bg)&65535;
                    ui::TextStyle s{size,std::uint16_t(fg),bool(bold),bool(shadow),bool(outline),std::uint16_t(effect),gap};
                    auto text=unhex(encoded);font.draw_block(image,text,x,y,s,center);auto box=font.measure_block(text,s);
                    std::cout<<box.width<<' '<<box.height<<'\n';
                }else return 3;
                std::ofstream out(std::filesystem::path(argv[2])/(std::to_string(step)+".555"),std::ios::binary);
                for(auto p:image.pixels){out.put(static_cast<char>(p));out.put(static_cast<char>(p>>8));}
            }
            ++step;
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
