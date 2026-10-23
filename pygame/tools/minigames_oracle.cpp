// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only public-state timeline adapter. Asset boxes arrive as explicit numeric inputs.
#include "rich4/minigames.hpp"
#include <iostream>
#include <iterator>
#include <memory>
#include <sstream>

int main() {
    using namespace rich4::minigames;
    std::unique_ptr<Penguin> penguin;
    std::unique_ptr<Balloon> balloon;
    std::unique_ptr<Catcher> catcher;
    Base *base=nullptr;
    int kind=-1;
    std::string line;
    while(std::getline(std::cin,line)) {
        std::istringstream in(line);char op;in>>op;
        std::vector<long long> n{std::istream_iterator<long long>(in),{}};
        int status=0,value=0;
        try {
            if(op=='n') {
                const int next=n.at(0);
                if(next==0){penguin=std::make_unique<Penguin>(n.at(1));base=penguin.get();}
                else if(next==1){balloon=std::make_unique<Balloon>(n.at(1));base=balloon.get();}
                else {
                    std::vector<Box> boxes;
                    for(unsigned i=0;i<unsigned(n.at(4));++i)boxes.push_back({int(n.at(5+i*4)),int(n.at(6+i*4)),int(n.at(7+i*4)),int(n.at(8+i*4))});
                    catcher=std::make_unique<Catcher>(n.at(1),n.at(2),boxes,n.at(3));base=catcher.get();
                }
                kind=next;
            }else if(op=='t'){if(kind==0)penguin->tick();else if(kind==1)balloon->tick();else catcher->tick();}
            else if(op=='b'){if(kind==0)penguin->begin_play();else base->begin_play();}
            else if(op=='p'){if(kind==0)value=penguin->tap(n.at(0),n.at(1));else if(kind==1)value=balloon->tap(n.at(0),n.at(1));else catcher->set_target(n.at(0));}
            else if(op=='a'){if(kind==0)penguin->tap_anywhere();}
            else if(op=='d')value=Catcher::drift(n.at(0));
            else if(op=='v')value=Penguin::valid(n.at(0),n.at(1));
            else return 3;
        }catch(const std::out_of_range &){status=2;}
        catch(const std::invalid_argument &){status=1;}
        if(!base)return 2;
        std::cout<<status<<' '<<value<<' '<<kind<<' '<<int(base->stage())<<' '<<base->draws()<<' '<<base->random_state()<<' '<<base->ticks_left();
        if(kind==0){
            auto &g=*penguin;auto [x,y]=g.position();
            std::cout<<' '<<g.score()<<' '<<x<<' '<<y<<' '<<g.idle()<<' '<<g.score_shown();
            for(auto v:g.found())std::cout<<' '<<v;
            std::cout<<' '<<g.holes().size();for(auto [a,b]:g.holes())std::cout<<' '<<a<<' '<<b;
            for(int y=0;y<9;++y)for(int x=0;x<9;++x){auto &c=g.cell(x,y);std::cout<<' '<<c.x<<' '<<c.y<<' '<<c.flags;}
        }else if(kind==1){
            auto &g=*balloon;std::cout<<' '<<g.score()<<' '<<g.freeze()<<' '<<g.speed_modifier();
            for(auto &s:g.slots())std::cout<<' '<<s.x<<' '<<s.y<<' '<<s.kind;
        }else {
            auto &g=*catcher;std::cout<<' '<<g.score()<<' '<<g.catcher_x()<<' '<<g.god_x();
            for(auto v:g.caught())std::cout<<' '<<v;
            auto explosion=g.explosion();std::cout<<' '<<bool(explosion);if(explosion)std::cout<<' '<<explosion->first<<' '<<explosion->second;
            for(auto &s:g.slots())std::cout<<' '<<s.x<<' '<<s.y<<' '<<s.bits<<' '<<s.vy;
        }
        std::cout<<' '<<base->scene().size();for(auto &s:base->scene())std::cout<<' '<<int(s.archive)<<' '<<s.entry<<' '<<s.frame<<' '<<s.x<<' '<<s.y<<' '<<s.scale;
        auto cues=base->drain_cues();std::cout<<' '<<cues.size();for(auto &c:cues)std::cout<<' '<<int(c.op)<<' '<<c.effect;
        std::cout<<'\n';
    }
}
