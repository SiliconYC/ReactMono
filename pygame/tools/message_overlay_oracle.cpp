// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only fixed messages.cpp; virtual SDL tick symbol, actual external fonts and artwork.
#include "screens/messages.hpp"
#include <iostream>
#include <sstream>
std::uint64_t test_ticks=0;
extern "C" std::uint64_t SDL_GetTicks(){return test_ticks;}
namespace {
std::string unhex(const std::string &s){if(s=="-")return {};std::string r;for(std::size_t i=0;i<s.size();i+=2)r.push_back(char(std::stoi(s.substr(i,2),nullptr,16)));return r;}
std::string hex(std::string_view s){if(s.empty())return "-";constexpr char h[]="0123456789abcdef";std::string r;for(unsigned char c:s){r+=h[c>>4];r+=h[c&15];}return r;}
}
int main(int argc,char **argv){
    if(argc!=3)return 2;
    try{
        using namespace rich4;using namespace native::messages;
        native::Artwork art(argv[1]);ui::Font font(argv[2]);auto canvas=graphics::make_canvas(640,480,0);
        std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);std::vector<int> calls;
        Overlay overlay({[&](auto v){calls.push_back(int(v));return unsigned(v*37%3200);},[&]{calls.push_back(-1);}});
        unsigned step=0;std::string line;auto p=[](auto v){std::cout<<' '<<static_cast<long long>(v);};
        while(std::getline(std::cin,line)){
            std::istringstream in(line);char op;in>>op;calls.clear();int result=-1;
            for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;
            if(op=='P'){
                Item x;int kind,ch,mood,focus;std::string text,title;
                in>>kind>>ch>>mood>>x.pictogram>>x.voice>>x.minimum_ms>>x.wait_voice>>focus>>x.box_x>>x.photo>>text>>title;
                x.kind=Item::Kind(kind);x.character=ch;x.mood=mood;x.focus=focus<0?std::nullopt:std::optional<std::size_t>(focus);x.text=unhex(text);x.title=unhex(title);
                unsigned n;in>>n;while(n--){int c,portrait;std::string t;in>>c>>portrait>>t;x.rows.push_back({std::uint8_t(c),portrait,unhex(t)});}
                overlay.push(x);
            }else if(op=='A')in>>test_ticks;
            else if(op=='B'){f.ticks=test_ticks;result=overlay.draw(f);}
            else if(op=='R')overlay.retire();
            else if(op=='C')overlay.clear();
            else if(op=='K')overlay.skip();
            else if(op=='S'){bool v;in>>v;overlay.set_instant(v);}
            else if(op=='H'){int id;in>>id;for(auto &b:buttons)if(b.id==id){auto action=b.action;buttons.clear();action();break;}}
            else if(op=='Y'){
                int mode,x,y;std::string t;in>>mode>>x>>y>>f.pointer_x>>f.pointer_y>>t;
                buttons.clear();
                if(mode)draw_yes_no(f,unhex(t),71,[&]{calls.push_back(71);},72,[&]{calls.push_back(72);});
                else draw_yes_no_strip(f,x,y,71,[&]{calls.push_back(71);},72,[&]{calls.push_back(72);});
            }else if(op=='T'){
                int mode,x,y,size;unsigned flags;std::string t;in>>mode>>x>>y>>size>>flags>>t;
                draw_text(f,unhex(t),x,y,mode,ui::TextStyle{size,ui::color(240,240,240),bool(flags&2),bool(flags&1),bool(flags&4),ui::color(16,16,16)});
            }else return 3;
            std::cout<<result;p(test_ticks);p(overlay.active());p(overlay.focus()?static_cast<long long>(*overlay.focus()):-1);
            p(overlay.started_);p(overlay.instant_);p(overlay.until_);std::cout<<' '<<hex(overlay.last_bubble_);p(overlay.photos_.size());
            p(overlay.queue_.size());for(const auto &x:overlay.queue_){p(x.kind);p(x.focus?static_cast<long long>(*x.focus):-1);p(x.character);p(x.mood);p(x.pictogram);p(x.voice);p(x.minimum_ms);p(x.wait_voice);p(x.box_x);p(x.photo);std::cout<<' '<<hex(x.text)<<' '<<hex(x.title);p(x.rows.size());for(const auto &r:x.rows){p(r.character);p(r.portrait_frame);std::cout<<' '<<hex(r.text);}}
            p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
            p(calls.size());for(auto c:calls)p(c);std::cout<<'\n';for(auto v:canvas.pixels){std::cout.put(char(v));std::cout.put(char(v>>8));}std::cout.flush();++step;
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
