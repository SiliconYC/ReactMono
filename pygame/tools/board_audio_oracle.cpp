// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: original inline board_audio policies with a request-recording Audio sink.
// This sink is NOT the original mixer and is never linked into the Python game.
#include "board_audio.hpp"
#include "native_frame.hpp"
#include <iostream>
#include <sstream>
namespace {std::vector<std::pair<int,int>> calls;}
namespace rich4::audio {
struct Audio::Impl {};
Audio::Audio(const std::filesystem::path &,bool,const std::filesystem::path &):impl_(std::make_unique<Impl>()){}
Audio::~Audio()=default;
void Audio::push_music(Music m){calls.emplace_back(0,int(m));}
void Audio::replace_music(Music m){calls.emplace_back(1,int(m));}
void Audio::pop_music(){calls.emplace_back(2,0);}
void Audio::play_loop(std::size_t n,Loop c){calls.emplace_back(3+int(c),int(n));}
void Audio::stop_loop(Loop c){calls.emplace_back(6+int(c),0);}
}
int main(int argc,char **argv){
 if(argc!=2)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;native::Artwork art(argv[1]);World world;audio::Audio sink({},false);native::MusicDirector music;native::WalkSound walk;
  auto p=[](auto n){std::cout<<' '<<n;};std::string line;
  while(std::getline(std::cin,line)){
   char op;std::istringstream in(line);in>>op;calls.clear();int a=-1,b=-1;
   auto old=world.nodes.empty()?std::vector<std::uint8_t>{}:world.export_save();
   if(op=='N'){unsigned m;in>>m;NewGameOptions opt;opt.map_id=m%4;opt.stage_id=m/4;world=World::from_map_resource(art.archive('m').decode(m*2+1),opt);music={};walk={};}
   else if(op=='V'){unsigned slot,node,traffic,bomb;in>>slot>>node>>traffic>>bomb;if(slot<4){auto &p=world.players.at(slot);p.state.node_id=node;p.state.traffic_method=traffic;p.status.attached_bomb=bomb;}else world.special_actors.at(slot-4).node_id=node;}
   else if(op=='P'){unsigned slot;in>>slot;if(auto n=native::walk_loop_clip(world,slot))a=int(*n);if(auto n=native::bomb_loop_clip(world,slot))b=int(*n);}
   else if(op=='H'){unsigned y,m,d,map,stage;in>>y>>m>>d>>map>>stage;world.header.date={std::uint8_t(d),std::uint8_t(m),std::uint16_t(y)};world.header.map_id=map;world.header.stage_id=stage;if(auto n=native::holiday_music(world))a=int(*n);}
   else if(op=='Q'){unsigned kind,hospital;in>>kind>>hospital;GameDecision d;d.kind=DecisionKind(kind);d.prompt=hospital?"探望住院角色":"other";if(auto n=native::decision_music(d))a=int(*n);}
   else if(op=='M'){std::uint64_t now;unsigned count,v;in>>now>>count;std::vector<audio::Music> wanted;for(unsigned i=0;i<count;++i){in>>v;wanted.push_back(audio::Music(v));}music.update(sink,wanted,now);}
   else if(op=='W'){std::uint64_t now;int w,b;in>>now>>w>>b;walk.update(sink,w<0?std::nullopt:std::optional<std::size_t>(w),b<0?std::nullopt:std::optional<std::size_t>(b),now);}
   else if(op=='F')music.forget();
   else if(op=='S')walk.stop(sink);
   else if(op=='R'){music={};walk={};}
   else return 3;
   auto dat=world.export_save();if(op!='N'&&op!='V'&&op!='H'&&dat!=old)throw std::runtime_error("audio policy changed World DAT");
   std::cout<<a;p(b);p(music.pushed_.size());for(auto n:music.pushed_)p(int(n));p(music.pop_pending_);p(music.pop_since_);p(walk.last_walk_);p(calls.size());for(auto [a,b]:calls){p(a);p(b);}p(dat.size());std::cout<<'\n';std::cout.write(reinterpret_cast<const char*>(dat.data()),dat.size());std::cout.flush();
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
