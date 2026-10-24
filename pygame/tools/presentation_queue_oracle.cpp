// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: explicit output fixtures, original observation/pump source seams, capture-only hosts.
#include "rich4/game.hpp"
#include "screens/spinners.hpp"
#include "screens/monthly.hpp"
#include "src/game.cpp"
#include <iostream>
#include <sstream>
using namespace rich4;
namespace spinners = rich4::native::spinners;
#include "presentation_handles.inc"
class Harness {
public:
    struct PresentationStep{std::optional<GameEvent> event;std::optional<EffectEvent> effect;};
    struct Options{unsigned auto_rounds=0;bool play_effects=true;} options_;
    struct Capture {
        Harness *h;int type;
        void enqueue(EffectEvent e){h->calls.push_back({type,int(e.kind),0});if(h->block)h->busy=true;}
        void enqueue(std::vector<EffectEvent> es,const void *){for(auto &e:es)enqueue(e);}
        void observe(const GameEvent &e,const World &){h->calls.push_back({0,int(e.kind),int(e.player)});}
    } spinners_{this,2},monthly_{this,3},effects_{this,4},items_{this,0};
    std::unique_ptr<GameSession> session_;
    std::deque<PresentationStep> presentation_;
    unsigned hold_ms_=0;bool bankrupt_music_=false,busy=false,block=false;
    std::optional<std::size_t> presented_player_;
    std::vector<std::array<int,3>> calls;
    bool presenting(){return hold_ms_>0||busy;}
    void present(const GameEvent &event){
#include "presentation_present.inc"
        calls.push_back({1,int(event.kind),int(event.player)});if(block)busy=true;
    }
#include "presentation_pump.inc"
#include "presentation_observe.inc"
};
int main(int argc,char **argv){
    if(argc!=2)return 2;
    try{
        assets::Archive maps(ui::asset_path(argv[1],"map.mkf"));Harness h;std::string line;
        auto p=[](auto v){std::cout<<' '<<static_cast<long long>(v);};
        while(std::getline(std::cin,line)){
            std::istringstream in(line);char op;in>>op;h.calls.clear();
            if(op=='N'){
                h.session_=std::make_unique<GameSession>(World::from_map_resource(maps.decode(1),NewGameOptions{}),1);
                (void)h.session_->drain_events();(void)h.session_->drain_effects();h.presentation_.clear();h.hold_ms_=0;h.bankrupt_music_=h.busy=h.block=false;h.presented_player_.reset();
            }else if(op=='Q'){
                unsigned events,effects;in>>events>>effects;auto &g=*h.session_->impl_;g.events.clear();g.effects.clear();
                while(events--){unsigned kind,player;in>>kind>>player;GameEvent e;e.kind=GameEventKind(kind);e.player=player;g.events.push_back(e);}
                while(effects--){unsigned kind,obj,after,flags;in>>kind>>obj>>after>>flags;EffectEvent e;e.kind=EffectKind(kind);e.object_kind=obj;e.after_events=after;if(flags&1)e.spinner=SpinnerState{};if(flags&2)e.monthly=MonthlyFigures{};g.effects.push_back(e);}
            }else if(op=='B')in>>h.busy;
            else if(op=='M')in>>h.block;
            else if(op=='H'){unsigned dt;in>>dt;h.hold_ms_-=std::min(h.hold_ms_,dt);}
            else if(op=='P'||op=='O'){
                in>>h.options_.auto_rounds>>h.options_.play_effects;
                if(op=='P')h.pump_presentation();else h.observe();
            }else return 3;
            std::cout<<0;p(h.hold_ms_);p(h.bankrupt_music_);p(h.presented_player_?static_cast<long long>(*h.presented_player_):-1);p(h.busy);p(h.presentation_.empty()&&!h.presenting());
            p(h.presentation_.size());for(auto &x:h.presentation_){p(bool(x.event));if(x.event){p(x.event->kind);p(x.event->player);}p(bool(x.effect));if(x.effect){p(x.effect->kind);p(x.effect->object_kind);p(x.effect->after_events);p(bool(x.effect->spinner));p(bool(x.effect->monthly));}}
            p(h.calls.size());for(auto &x:h.calls)for(auto v:x)p(v);p(h.session_->impl_->events.size());p(h.session_->impl_->effects.size());std::cout<<'\n'<<std::flush;
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
