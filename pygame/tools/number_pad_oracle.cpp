// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: actual original NumberPad, real artwork, keyboard/pointer/button callbacks.
#include "screens/finance.hpp"
#include <iostream>
#include <sstream>
int main(int argc,char **argv){
    if(argc!=3)return 2;
    try{
        using namespace rich4;native::Artwork art(argv[1]);ui::Font font(argv[2]);
        auto canvas=graphics::make_canvas(640,480,0);std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);
        std::vector<int> sounds,done;native::screens::Host host{f,[&](auto n){sounds.push_back(n);},{}};
        native::screens::NumberPad pad;unsigned step=0;std::string line;auto p=[](auto v){std::cout<<' '<<static_cast<long long>(v);};
        while(std::getline(std::cin,line)){
            std::istringstream in(line);char op;in>>op;sounds.clear();done.clear();int result=-1;
            if(op=='S'){int n;in>>n;pad.set_scale(n);}
            else if(op=='O'){int maximum,next;in>>maximum>>next;pad.open(maximum,[&,next](int v){done.push_back(v);if(next>=0)pad.open(next,[&](int n){done.push_back(n);});});}
            else if(op=='D'){in>>f.pointer_x>>f.pointer_y>>f.pointer_down;for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;buttons.clear();pad.draw(host);}
            else if(op=='K'){int key;in>>key;pad.key(host,char(key));}
            else if(op=='X'){int id;in>>id;for(auto &b:buttons)if(b.id==id&&b.enabled){auto action=b.action;buttons.clear();action();break;}}
            else if(op=='Q'){int n;in>>n;result=pad.next_key_towards(n);}
            else if(op=='B')pad.cancel(host);
            else if(op=='C')pad.close();
            else if(op=='I'){int n;in>>n;result=native::screens::ids::pad_digit(n);}
            else return 3;
            std::cout<<result;p(pad.active_);p(pad.dragging_);p(pad.x_);p(pad.y_);p(pad.scale());p(pad.prompt_top());p(pad.maximum());p(pad.value());std::cout<<' '<<pad.digits();p(bool(pad.done_));
            p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
            p(sounds.size());for(auto n:sounds)p(n);p(done.size());for(auto n:done)p(n);std::cout<<'\n';
            if(op=='D')for(auto v:canvas.pixels){std::cout.put(char(v));std::cout.put(char(v>>8));}std::cout.flush();++step;
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
