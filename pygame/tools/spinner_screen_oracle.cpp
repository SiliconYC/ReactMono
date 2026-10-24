// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: fixed original Spinners and real external font/artwork; private RNG and sound callbacks observed.
#include "screens/spinners.hpp"
#include <iostream>
#include <sstream>
extern "C" std::uint64_t SDL_GetTicks(){return 0;}
int main(int argc,char **argv){
    if(argc!=3)return 2;
    try{
        using namespace rich4;native::Artwork art(argv[1]);ui::Font font(argv[2]);World world;
        auto canvas=graphics::make_canvas(640,480,0);std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);
        std::vector<std::pair<int,int>> calls;std::unique_ptr<native::spinners::Spinners> screen;
        auto p=[](auto v){std::cout<<' '<<static_cast<long long>(v);};
        auto state=[&](const SpinnerState &s){p(s.type);for(auto n:s.digits)p(n);p(s.phase);p(s.cursor);p(s.subject);p(s.seed);p(s.result);};
        auto read_state=[&](std::istringstream &in){SpinnerState s;unsigned type,phase,cursor,n;in>>type;for(auto &d:s.digits){in>>n;d=n;}in>>phase>>cursor>>s.subject>>s.seed>>s.result;s.type=type;s.phase=phase;s.cursor=cursor;return s;};
        unsigned step=0;std::string line;
        while(std::getline(std::cin,line)){
            std::istringstream in(line);char op;in>>op;calls.clear();int result=-1;
            for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;
            if(op=='N'){
                unsigned map,ch;in>>map>>ch;NewGameOptions opt;opt.map_id=map%4;opt.stage_id=map/4;opt.players[0].character=ch;
                world=World::from_map_resource(art.archive('m').decode(map*2+1),opt);buttons.clear();
                screen=std::make_unique<native::spinners::Spinners>(native::spinners::Sound{[&](auto n){calls.emplace_back(0,n);},[&](auto n){calls.emplace_back(1,n);},[&]{calls.emplace_back(2,0);}});
            }else if(op=='E'||op=='D'){
                unsigned kind,has;in>>kind>>has;auto s=read_state(in);
                if(op=='E'){EffectEvent e;e.kind=EffectKind(kind);if(has)e.spinner=s;screen->enqueue(e);}
                else {GameDecision d;d.kind=DecisionKind(kind);d.player=0;d.spinner=s;buttons.clear();screen->draw_decision(f,world,d,901,[&]{calls.emplace_back(3,901);});}
            }else if(op=='F'){unsigned dt;in>>dt;buttons.clear();screen->draw_effect(f,world,dt,901);}
            else if(op=='Z')screen->finish_frame();
            else if(op=='S'){bool skip;in>>skip;screen->set_skip(skip);}
            else if(op=='C')screen->clear();
            else if(op=='X'){int id;in>>id;for(auto &b:buttons)if(b.id==id){auto action=b.action;buttons.clear();action();break;}}
            else if(op=='V'){unsigned kind,has,decision;in>>kind>>has>>decision;EffectEvent e;e.kind=EffectKind(kind);if(has)e.spinner=SpinnerState{};GameDecision d;d.kind=DecisionKind(kind);if(has)d.spinner=SpinnerState{};result=decision?native::spinners::handles(d):native::spinners::handles(e);}
            else return 3;
            std::cout<<result;p(screen->skip_);p(screen->wanted_loop_);p(screen->playing_loop_);p(screen->decision_phase_);p(screen->queue_.size());
            for(auto &e:screen->queue_){p(e.kind);p(bool(e.spinner));if(e.spinner)state(*e.spinner);}
            p(bool(screen->current_));if(screen->current_){auto &x=*screen->current_;p(x.event.kind);state(*x.event.spinner);state(x.state);p(x.elapsed);p(x.frames);p(x.wheel_state);p(x.period);p(x.count);p(x.last);p(x.random.state());p(x.skip);p(bool(x.machine));if(x.machine){auto &m=*x.machine;for(auto d:m.digits_)p(d);p(m.omitted_digit_);p(m.phase_);p(m.frames_);p(m.slowing_period_);p(m.slowing_elapsed_);p(m.last_slowing_digit_);}}
            p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
            p(calls.size());for(auto [k,n]:calls){p(k);p(n);}std::cout<<'\n';
            if(op=='F'||op=='D')for(auto v:canvas.pixels){std::cout.put(char(v));std::cout.put(char(v>>8));}std::cout.flush();++step;
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
