// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only fixed EffectPlayer/Renderer with external assets; no game backend in Python runtime.
#include "screens/effects.hpp"
#include <iostream>
#include <sstream>
int main(int argc,char **argv){
    if(argc!=2)return 2;
    try{
        using namespace rich4;
        native::Artwork art(argv[1]);std::unique_ptr<GameSession> game;
        std::unique_ptr<board::Renderer> board;std::unique_ptr<native::EffectPlayer> player;
        World world;auto canvas=graphics::make_canvas(640,480,0);
        std::vector<int> sounds;std::uint64_t ticks=0;unsigned step=0;std::string line;
        auto p=[](auto v){std::cout<<' '<<static_cast<long long>(v);};
        auto event=[&](unsigned kind,unsigned obj,unsigned direction){
            EffectEvent e;e.kind=EffectKind(kind);e.player=0;e.node=1;e.property=world.lands.size()>1?2001:4001;
            e.target=world.lands.size()>1?EffectPoint{world.lands[1].x,world.lands[1].y}:EffectPoint{world.facilities[1].x,world.facilities[1].y};e.from=EffectPoint{world.players[0].state.x,world.players[0].state.y};
            e.object_kind=obj;e.direction=direction;e.previous_level=3;e.previous_type=0;return e;
        };
        while(std::getline(std::cin,line)){
            std::istringstream in(line);char op;in>>op;sounds.clear();
            for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;
            if(op=='I'){
                unsigned map,ch,traffic;in>>map>>ch>>traffic;NewGameOptions opt;opt.map_id=map%4;opt.stage_id=map/4;
                opt.players[0].character=ch;opt.players[0].traffic_method=traffic;
                game=std::make_unique<GameSession>(World::from_map_resource(art.archive('m').decode(map*2+1),opt),1);world=game->world();
                board=std::make_unique<board::Renderer>(argv[1],map);player=std::make_unique<native::EffectPlayer>(art);ticks=0;
                const auto target=event(0,0,0).target;auto &state=world.players[0].state;state.x=std::max(0,target.x-64);state.y=std::max(0,target.y-32);state.controller_flags=1;state.node_id=1;
                if(world.lands.size()>1){world.lands[1].economy.owner_code=2;world.lands[1].economy.level=3;}else{world.facilities[1].owner_code=2;world.facilities[1].level=3;world.facilities[1].facility_type=0;}
                const std::array<std::uint8_t,4> costumes{0,18,19,0};player->set_costumes(costumes);player->remember(world,game.get(),ticks);
            }else if(op=='E'){
                unsigned kind,obj,direction;in>>kind>>obj>>direction;auto e=event(kind,obj,direction);
                if(world.lands.size()>1){world.lands[1].economy.owner_code=1;world.lands[1].economy.level=0;}else{world.facilities[1].owner_code=1;world.facilities[1].level=0;}
                const auto spec=native::effect_spec(e);
                if(spec.actor==native::EffectSpec::Actor::leave||spec.actor==native::EffectSpec::Actor::stay)
                    world.players[0].status.days_in_hospital=3;
                if(spec.actor==native::EffectSpec::Actor::arrive)world.players[0].status.days_in_hospital=0;
                if(e.kind==EffectKind::truck_demolish)world.players[0].state.traffic_method=3;
                if(e.kind==EffectKind::object_throw){auto &o=world.objects.back();o.kind=obj;o.node_id=e.node;o.attached_player=0;o.direction=direction;}
                player->enqueue({e},game.get());
            }else if(op=='D'||op=='L'){
                unsigned dt,rotation;in>>dt>>rotation;ticks+=dt;
                if(op=='D')player->draw(canvas,*board,world,rotation,dt,ticks,[&](auto n){sounds.push_back(n);});
                else player->draw_linger(canvas,*board,world,rotation,ticks);
            }else if(op=='P'){unsigned slot,kind;in>>slot>>kind;std::vector<native::PendingActor> pending;auto e=event(kind,0,0);e.player=slot;native::add_pending_actor(pending,e);player->set_pending_actors(std::move(pending));
            }else if(op=='S'){bool skip;in>>skip;player->set_skip(skip);
            }else if(op=='M')player->remember(world,game.get(),ticks);
            else if(op=='N')game=std::make_unique<GameSession>(world,1);
            else if(op=='X')player->drop_linger();
            else if(op=='C')player->clear();
            else return 3;
            std::cout<<0;p(ticks);p(player->active());p(player->lingering());p(player->skip_);p(bool(player->snapshot_));
            p(player->queue_.size());for(auto &e:player->queue_){p(e.kind);p(e.object_kind);p(e.direction);}
            p(bool(player->current_));if(player->current_){auto &x=*player->current_;p(x.event.kind);p(x.elapsed);p(x.delay);p(x.sounded);p(bool(x.movie));if(x.movie){p(x.movie->decoded_frames());p(x.movie->frame_count());}p(x.frame.width);p(x.frame.height);p(x.path.size());for(auto pt:x.path){p(pt.x);p(pt.y);}}
            p(bool(player->lingering_));if(player->lingering_){auto &x=*player->lingering_;p(x.event.kind);p(x.elapsed);p(x.sounded);p(x.movie?x.movie->decoded_frames():0);p(x.frame.width);p(x.frame.height);}
            p(sounds.size());for(auto n:sounds)p(n);std::cout<<'\n';
            for(auto v:canvas.pixels){std::cout.put(char(v));std::cout.put(char(v>>8));}std::cout.flush();++step;
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
