// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: original facility picker and AiSettingsScreen, real artwork/font and GameSession settings source.
#include "screens/facility.hpp"
#include "screens/ai_settings.hpp"
#include <iostream>
#include <sstream>
extern "C" std::uint64_t SDL_GetTicks(){return 0;}
int main(int argc,char **argv){
 if(argc!=3)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;native::Artwork art(argv[1]);ui::Font font(argv[2]);World world;std::unique_ptr<GameSession> game;
  auto canvas=graphics::make_canvas(640,480,0);std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);
  native::facility::Picker picker;native::screens::AiSettingsScreen ai;GameDecision decision;std::vector<std::vector<long long>> calls;
  native::screens::Host host{f,[&](auto n){calls.push_back({0,n});},{}};
  auto settings=[](const AiSettings &s){return std::vector<long long>{s.autopilot,s.card_strategy,s.personality,s.cash_ratio,s.stock_ratio};};
  native::screens::AiSettingsActions actions{[&](auto slot,const auto &s){auto v=settings(s);v.insert(v.begin(),slot);v.insert(v.begin(),2);calls.push_back(v);},[&]{calls.push_back({3,0});}};
  auto respond=[&](auto n){calls.push_back({1,static_cast<long long>(n)});};
  auto p=[](auto n){std::cout<<' '<<static_cast<long long>(n);};
  auto str=[&](const std::string &s){std::uint64_t h=14695981039346656037ULL;for(unsigned char c:s){h^=c;h*=1099511628211ULL;}p(s.size());std::cout<<' '<<h;};
  unsigned step=0;std::string line;
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;calls.clear();int result=-1;std::vector<std::uint8_t> old;std::uint32_t rng=game?game->random_state():0;
   if(op=='F'||op=='D'||op=='X'||op=='B'||op=='E'||op=='O')old=game->world().export_save();
   if(op=='N'){
    unsigned map,ch,mask;in>>map>>ch>>mask;NewGameOptions opt;opt.map_id=map%4;opt.stage_id=map/4;
    for(unsigned i=0;i<4;++i){opt.players[i].character=(ch+3*i)%12;opt.players[i].controller=(mask&(1<<i))?1:2;}
    world=World::from_map_resource(art.archive('m').decode(map*2+1),opt);game=std::make_unique<GameSession>(std::move(world));picker={};ai={};buttons.clear();decision={};
   }else if(op=='Q'){
    unsigned kind,valid,count;in>>kind>>valid>>count;decision={};decision.kind=DecisionKind(kind);decision.prompt=valid?"請選擇設施類別":"other";
    for(unsigned i=0;i<count;++i){int v,loc;in>>v>>loc;DecisionOption o{"",v};if(loc)o.location=DecisionLocation{0,0};decision.options.push_back(o);}
    result=native::facility::handles(decision)*2+native::facility::Picker::cancellable(decision);
   }else if(op=='F'||op=='D'){
    std::string key;in>>f.ticks>>f.pointer_x>>f.pointer_y>>f.pointer_down>>key;
    for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;buttons.clear();
    if(op=='F')picker.draw(host,decision,key,respond);else ai.draw(host,game->world(),actions);
   }else if(op=='O'){long long n;in>>n;result=ai.open(*game,static_cast<std::size_t>(n));}
   else if(op=='V'){
    unsigned slot,on,cards,pers,cash,stock;in>>slot>>on>>cards>>pers>>cash>>stock;
    AiSettings s{on!=0,static_cast<std::uint8_t>(cards),static_cast<std::uint8_t>(pers),static_cast<std::uint8_t>(cash),static_cast<std::uint8_t>(stock)};ai.edits_.at(slot)=s;
   }else if(op=='X'){int id;in>>id;for(auto &b:buttons)if(b.id==id&&b.enabled){auto a=b.action;buttons.clear();a();break;}}
   else if(op=='B')picker.cancel(host,decision,respond);
   else if(op=='E')ai.cancel(host,actions);
   else return 3;
   if(!old.empty()&&(old!=game->world().export_save()||rng!=game->random_state()))throw std::runtime_error("UI changed World DAT before commit");
   std::cout<<result;p(game->random_state());p(game->phase());str(picker.key_);p(picker.selected_?*picker.selected_:-1);p(ai.selected_);
   for(auto *a:{&ai.edits_,&ai.original_})for(auto &s:*a){p(bool(s));if(s)for(auto v:settings(*s))p(v);}
   p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
   p(calls.size());for(auto &c:calls){p(c.size());for(auto v:c)p(v);}std::cout<<'\n';
   if(op=='D'||op=='F'){std::vector<char> raw;raw.reserve(canvas.pixels.size()*2);for(auto v:canvas.pixels){raw.push_back(char(v));raw.push_back(char(v>>8));}std::cout.write(raw.data(),raw.size());}std::cout.flush();++step;
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
