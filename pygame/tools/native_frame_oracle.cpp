// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only fixed Frame/screens::draw, all commercial pixels remain in local temporary storage.
#include "screens/draw.hpp"
#include <fstream>
#include <iostream>
#include <sstream>
static std::string unhex(const std::string &v) {
    if(v=="-")return {};std::string s;
    for(std::size_t i=0;i<v.size();i+=2)s.push_back(char(std::stoul(v.substr(i,2),nullptr,16)));
    return s;
}
int main(int argc,char **argv) {
    if(argc!=4)return 2;
    try {
        using namespace rich4; namespace d=native::screens;
        native::Artwork art(argv[1]);ui::Font font(argv[2]);
        std::filesystem::create_directories(argv[3]);
        unsigned step=0;std::string line;
        while(std::getline(std::cin,line)) {
            std::istringstream in(line);char op;unsigned seed;in>>op>>seed;
            auto image=graphics::make_canvas(640,480,0);
            for(std::size_t i=0;i<image.pixels.size();++i)image.pixels[i]=(i*1103515245ULL+seed)&65535;
            std::vector<native::Button> buttons;native::Frame f(image,art,font,buttons);
            std::vector<int> actions,sounds;int measured=-1;std::string money="-";
            if(op=='B'||op=='D') {
                int x,y,r,b,enabled;std::string h;in>>x>>y>>r>>b>>enabled>>h;
                if(op=='B')f.button(71,{x,y,r,b},unhex(h),[&]{actions.push_back(71);},enabled);
                else f.dialog({x,y,r,b},unhex(h));
            }else if(op=='T'||op=='F'||op=='Z') {
                int x,y,align,size,flags;unsigned fg,bg;std::string h;
                in>>x>>y>>align>>size>>fg>>bg>>flags>>h;auto text=unhex(h);
                if(op=='T'){d::Style style{size,fg,bg,flags};d::text(f,text,x,y,align,style);measured=d::measure(f,text,style);}
                else if(op=='F')f.text(text,x,y,size,fg,align);
                else f.centered(text,x,y,size,fg);
            }else if(op=='X'||op=='Y'||op=='V'||op=='Q') {
                int x,y,r,b,level;in>>x>>y>>r>>b>>level;
                if(op=='X')d::darken(image,{x,y,r,b},level);
                else if(op=='Y')d::greyscale(image,{x,y,r,b});
                else if(op=='V')d::pressed_bevel(image,{x,y,r,b});
                else d::outline_rect(image,{x,y,r,b},level);
            }else if(op=='A'||op=='L'||op=='U'||op=='O') {
                char archive;unsigned entry,index;int x,y,scale,l,t,r,b;
                in>>archive>>entry>>index>>x>>y>>scale>>l>>t>>r>>b;
                if(op=='A')f.picture(archive,entry,index,x,y);
                else if(op=='L')d::blit_part(image,art.frame(archive,entry,index),{l,t,r,b},x,y);
                else if(op=='U')f.picture(d::scaled(art,archive,entry,index,scale),x,y);
                else d::backdrop(f,archive,entry,index);
            }else if(op=='H') {
                int effect,enabled;in>>effect>>enabled;
                d::Host host{f,[&](int s){sounds.push_back(s);},{}};
                d::hit(host,75,{3,4,50,60},effect,[&]{actions.push_back(75);},enabled);
                buttons[0].action();
            }else if(op=='E') {
                int year,month,day,map,stage;in>>year>>month>>day>>map>>stage;
                World world;world.header.date.year=year;world.header.date.month=month;world.header.date.day=day;
                world.header.map_id=map;world.header.stage_id=stage;
                auto picture=d::festival_picture(art,world);measured=bool(picture);
                if(picture)f.picture(*picture,20,30);
            }else if(op=='P') {
                int y;std::string encoded;in>>y>>encoded;
                d::Host host{f,{},{}};d::popup(host,unhex(encoded),y);
            }else if(op=='M') {
                long long amount;in>>amount;money=d::grouped(amount);
            }else return 3;
            std::cout<<measured<<' '<<buttons.size();
            for(auto &b:buttons)std::cout<<' '<<b.id<<' '<<b.rectangle.left<<' '<<b.rectangle.top<<' '<<b.rectangle.right<<' '<<b.rectangle.bottom<<' '<<b.enabled<<' '<<b.click_sound;
            std::cout<<' '<<actions.size();for(auto a:actions)std::cout<<' '<<a;
            std::cout<<' '<<sounds.size();for(auto s:sounds)std::cout<<' '<<s;std::cout<<' '<<money<<'\n';
            std::ofstream out(std::filesystem::path(argv[3])/(std::to_string(step++)+".555"),std::ios::binary);
            for(auto p:image.pixels){out.put(char(p));out.put(char(p>>8));}
            if(!out)throw std::runtime_error("pixel write failed");
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
