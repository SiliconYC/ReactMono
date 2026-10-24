// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: fixed original inventory/card popup and real GameSession actions; never a runtime backend.
#include "screens/items.cpp"
#include <sstream>
extern "C" std::uint64_t SDL_GetTicks(){return 0;}
int main(int argc,char **argv){
 if(argc!=3)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;using namespace native::items;native::Artwork art(argv[1]);ui::Font font(argv[2]);
  auto canvas=graphics::make_canvas(640,480,0);std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);
  Screens screen;std::unique_ptr<GameSession> game;std::vector<std::vector<long long>> calls;std::vector<std::string> texts;
  screen.sound=[&](auto n){calls.push_back({0,(long long)n});};screen.speech=[&](auto n,bool q){calls.push_back({1,(long long)n,q});};
  Host host{[&]{calls.push_back({2});},[&](bool ok,std::string_view text){calls.push_back({3,ok});texts.emplace_back(text);},[&](auto i){const bool ok=game->respond(i);calls.push_back({4,(long long)i,ok});return ok;}};
  auto p=[](auto n){std::cout<<' '<<static_cast<long long>(n);};auto str=[&](std::string_view s){std::uint64_t h=14695981039346656037ULL;for(unsigned char c:s){h^=c;h*=1099511628211ULL;}p(s.size());std::cout<<' '<<h;};
  auto image=[&](const graphics::Image &im){p(im.width);p(im.height);p(im.origin_x);p(im.origin_y);p(im.pixels.size());std::uint64_t h=14695981039346656037ULL;for(auto v:im.pixels)for(unsigned b:{unsigned(v&255),unsigned(v>>8)}){h^=b;h*=1099511628211ULL;}std::cout<<' '<<h;};
  unsigned step=0;std::string line;
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;calls.clear();texts.clear();std::vector<std::uint8_t> old;
   if(op=='D'||op=='P')old=game->world().export_save();
   if(op=='N'){
    unsigned m,ch;in>>m>>ch;NewGameOptions opt;opt.map_id=m%4;opt.stage_id=m/4;for(unsigned i=0;i<4;++i){opt.players[i].character=(ch+3*i)%12;opt.players[i].controller=1;}
    game=std::make_unique<GameSession>(World::from_map_resource(art.archive('m').decode(m*2+1),opt),1);screen.reset();buttons.clear();
   }else if(op=='W'){
    unsigned profile,vehicle;in>>profile>>vehicle;auto &p=const_cast<World&>(game->world()).active_player().state;p.cards={};p.tool_amounts={};p.traffic_method=vehicle;p.dice_count=1+(vehicle&3);
    if(profile){for(unsigned j=0;j<15;++j)p.cards[j]=1+j+(profile==2?15:0);for(unsigned j=0;j<13;++j)p.tool_amounts[j]=1+j%9;}
    if(profile==3)p.cards={0,1,14,14,18,30,31,0,20,2,255,15,0,9,8};
   }else if(op=='H'){unsigned slot,flags;in>>slot>>flags;const_cast<World&>(game->world()).players.at(slot).state.controller_flags=flags;}
   else if(op=='O'){unsigned slot,card;in>>slot>>card;GameEvent e{};e.player=slot;e.card=card;screen.observe(e,game->world());}
   else if(op=='G'){unsigned card,callback;in>>card>>callback;screen.popups_.push_back({std::uint8_t(card),0,callback?std::function<void()>([&]{calls.push_back({5});}):std::function<void()>{}});}
   else if(op=='C'){long long t;in>>t;if(t<0)screen.clock.reset();else screen.clock=t;}
   else if(op=='U')screen.run_deferred();
   else if(op=='R'){screen.reset();buttons.clear();}
   else if(op=='D'||op=='P'){
    bool cards=false;if(op=='D')in>>cards;in>>f.ticks>>f.pointer_x>>f.pointer_y>>f.pointer_down;
    for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;buttons.clear();screen.shot.clear();
    if(op=='D')screen.draw_inventory(f,*game,cards,host);else screen.draw_popup(f);
   }else if(op=='X'){int id;in>>id;bool found=false;for(auto &b:buttons)if(b.id==id&&b.enabled){found=true;auto a=b.action;buttons.clear();a();break;}if(!found)throw std::runtime_error("expected item button missing: "+std::to_string(id));}
   else return 3;
   auto dat=game->world().export_save();if(!old.empty()&&old!=dat)throw std::runtime_error("inventory/popup draw changed World DAT");
   std::cout<<-1;p(game->phase());p(game->random_state());p(bool(game->pending_decision()));
   if(game->pending_decision()){auto &d=*game->pending_decision();p(d.kind);p(d.player);p(d.land_id);p(d.amount);str(d.prompt);p(d.options.size());for(auto &o:d.options){str(o.label);p(o.value);p(bool(o.location));if(o.location){p(o.location->x);p(o.location->y);}p(bool(o.subject));if(o.subject){p(o.subject->kind);p(o.subject->value);}}p(d.max_amount);p(d.inactive_players);p(bool(d.victim));if(d.victim)p(*d.victim);}
   p(screen.popups_.size());for(auto &q:screen.popups_){p(q.card);p(q.until);p(bool(q.then));}p(screen.deferred_.size());p(bool(screen.press_));if(screen.press_){auto &q=*screen.press_;str(q.owner);p(q.rect.left);p(q.rect.top);p(q.rect.right);p(q.rect.bottom);p(bool(q.action));p(q.item);}
   p(screen.last_card_);p(screen.last_tool_);str(screen.voiced_);p(bool(screen.clock));if(screen.clock)p(*screen.clock);str(screen.shot);
   p(screen.descriptions_.size());for(auto &[k,v]:screen.descriptions_){p(k.first);p(k.second);str(v);}p(screen.card_art_.size());for(auto &[k,v]:screen.card_art_){p(k);image(v);}
   p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
   p(calls.size());for(auto &c:calls){p(c.size());for(auto n:c)p(n);}p(texts.size());for(auto &s:texts)str(s);p(dat.size());std::cout<<'\n';
   if(op=='D'||op=='P'){std::vector<char> raw;raw.reserve(canvas.pixels.size()*2);for(auto v:canvas.pixels){raw.push_back(char(v));raw.push_back(char(v>>8));}std::cout.write(raw.data(),raw.size());}
   std::cout.write(reinterpret_cast<const char*>(dat.data()),dat.size());std::cout.flush();++step;
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
