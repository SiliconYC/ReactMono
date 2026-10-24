// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: exact fixed scene helpers and effect table; explicit fixture mutations are not natural games.
#include "screens/effects.hpp"
#include <iostream>
#include <sstream>
using namespace rich4;
static void p(long long v){std::cout<<' '<<v;}
static void scene(const native::SceneData &s) {
    p(s.players.size());for(auto &x:s.players){p(x.position.x);p(x.position.y);p(x.character);p(x.direction);p(x.animation_frame);p(x.traffic_method);p(x.color);p(x.slot);p(x.active);p(x.walking);p(x.on_water);p(x.sleepwalking);p(x.injured);p(x.tossing);p(x.special_pose);}
    p(s.objects.size());for(auto &x:s.objects){p(x.position.x);p(x.position.y);p(x.kind);p(x.direction);p(x.animation_frame);p(x.follow);}
    auto properties=[](auto &list){p(list.size());for(auto &x:list){p(x.id);p(x.owner);p(x.level);p(x.type);p(x.temporary);}};
    properties(s.lands);properties(s.facilities);properties(s.commercials);
    p(s.special_players.size());for(auto &x:s.special_players){p(x.position.x);p(x.position.y);p(x.slot);p(x.direction);p(x.animation_frame);p(x.active);p(x.walking);p(x.on_water);p(x.sleepwalking);}
    p(s.owners.size());for(auto &x:s.owners){p(x.color);p(x.character);}
}
static void fixture(World &w,unsigned v) {
    constexpr unsigned controls[]{0,1,2,32,64,128,33,66};
    w.header.current_player=v%w.players.size();
    for(unsigned i=0;i<w.players.size();++i){auto &s=w.players[i].state;auto &t=w.players[i].status;
        s.x=(v*13+i*61)%2304;s.y=(v*17+i*43)%2304;s.direction=(v+i)&7;s.traffic_method=(v+i)%4;s.character=(v+i)%12;s.controller_flags=controls[(v+i)%8];s.node_id=1+(v+i)%(w.nodes.size()-1);
        t.days_in_hotel=(v>>0)&1;t.days_disappearing=(v>>1)&1;t.days_in_prison=(v>>2)&1;t.days_in_hospital=(v>>3)&1;t.days_sleep_walking=(v+i)%2;t.god_info=(v+i)%3;
        if((v+i)&1)w.nodes[s.node_id].flags|=0x80000000U;
    }
    for(unsigned i=0;i<w.objects.size();++i){auto &o=w.objects[i];o.kind=i<6?std::array<unsigned,6>{16,17,18,1,2,0}[i]:0;o.node_id=i<6?1+(v+i)%(w.nodes.size()-1):0;o.attached_player=i<6?(v+i)%7:0;o.direction=(v+i)&7;}
    for(unsigned i=0;i<w.special_actors.size();++i){auto &a=w.special_actors[i];a.inactive_state=(v+i)%3;a.node_id=1+(v+i)%(w.nodes.size()-1);a.x=(v*31+i*59)%2304;a.y=(v*19+i*41)%2304;a.direction=(v+i)&7;a.days_sleep_walking=(v+i)%2;}
    for(unsigned i=1;i<w.lands.size();++i){auto &a=w.lands[i];a.economy.owner_code=(i+v)%(w.players.size()+1);a.economy.level=(i+v)%6;a.economy.chain_store=(i+v)%2;a.temporary_state=(i+v*17)&255;}
    for(unsigned i=1;i<w.facilities.size();++i){auto &a=w.facilities[i];a.owner_code=(i+v)%(w.players.size()+1);a.level=(i+v)%6;a.temporary_state=(i+v*17)&255;}
    for(unsigned i=0;i<w.commercials.size();++i)w.commercials[i].owner_code=(i+v)%(w.players.size()+1);
}
int main(int argc,char **argv){
    if(argc!=2)return 2;
    try{
        assets::Archive maps(ui::asset_path(argv[1],"Map.mkf"));std::string line;
        while(std::getline(std::cin,line)){
            std::istringstream in(line);char op;in>>op;std::cout<<0;
            if(op=='S'){
                unsigned k,obj;in>>k>>obj;EffectEvent e;e.kind=EffectKind(k);e.object_kind=obj;
                auto s=native::effect_spec(e);p(s.archive);p(s.entry);p(s.commit_frame);p(s.sound);p(s.sound_frame);p(s.hold_ms);p(s.camera_on_target);p(s.x);p(s.y);p(int(s.actor));p(s.injured);p(s.linger);
            }else if(op=='W'){
                unsigned map,seed,v;std::uint64_t ticks;in>>map>>seed>>ticks>>v;
                auto w=[&]{if(map>=8)return World::from_save(SaveFile::decode(ui::read_file(ui::asset_path(argv[1],map==8?"Save0.dat":"SAVE1.DAT"))));
                    NewGameOptions opt;opt.map_id=map%4;opt.stage_id=map/4;opt.random_seed=seed;
                    GameSession game(World::from_map_resource(maps.decode(map*2+1),opt),seed);return game.world();}();
                fixture(w,v);auto before=w.export_save();
                const std::array<std::uint8_t,4> costumes{0,18,19,0};
                auto data=native::make_scene(w,ticks,costumes);scene(data);
                constexpr EffectKind kinds[]{EffectKind::ambulance,EffectKind::police,EffectKind::dog_fight,EffectKind::ufo,EffectKind::airplane,EffectKind::parachute};
                std::vector<native::PendingActor> pending;
                for(unsigned j=0;j<3;++j){EffectEvent e;e.kind=kinds[(v+j)%6];e.player=(v+j/2)%w.players.size();e.object_kind=(v+j)%2;if((v+j)%3)e.from=EffectPoint{int(v*7+j),int(v*11+j)};native::add_pending_actor(pending,e);}
                p(pending.size());for(auto &x:pending){p(x.slot);p(bool(x.position));if(x.position){p(x.position->x);p(x.position->y);}p(x.injured);}
                auto frame=std::uint8_t((ticks/120)%6);
                native::apply_pending_actors(data.players,w,pending,frame,costumes);
                data.objects=native::object_sprites(w,data.players,frame);
                native::hide_objects(data.objects,[](auto pos,auto kind){return kind==16;});
                scene(data);p(before==w.export_save());
            }else return 3;
            std::cout<<'\n'<<std::flush;
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
