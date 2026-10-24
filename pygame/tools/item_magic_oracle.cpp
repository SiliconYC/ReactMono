// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: original magic screens/real FLC plus real private visit/public responses; no runtime backend.
#include "game.cpp"
#include "screens/items.cpp"
#include <sstream>
#include <type_traits>
extern "C" std::uint64_t SDL_GetTicks(){return 0;}
template<class C> std::uint64_t magic_digest(const C &c){std::uint64_t h=14695981039346656037ULL;for(auto v:c)for(unsigned i=0;i<sizeof(v);++i){h^=(std::uint64_t(v)>>(i*8))&255;h*=1099511628211ULL;}return h;}
int main(int argc,char **argv){
 if(argc!=3)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;using namespace native::items;native::Artwork art(argv[1]);ui::Font font(argv[2]);
  flc::Decoder preflight(art.archive('p').decode(20));while(preflight.next()){}if(!preflight.frame_count()||preflight.decoded_frames()!=preflight.frame_count()||art.archive('p').decode(19).size()<307200)throw std::runtime_error("magic movie/mask preflight incomplete");
  auto canvas=graphics::make_canvas(640,480,0);std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);Screens screen;std::unique_ptr<GameSession> game;GameDecision fixture;bool real=false;
  std::vector<std::vector<long long>> calls;std::vector<std::string> texts;screen.sound=[&](auto n){calls.push_back({0,(long long)n});};screen.speech=[&](auto n,bool q){calls.push_back({1,(long long)n,q});};
  Host host{[&]{calls.push_back({4});},[&](bool ok,std::string_view t){calls.push_back({3,ok});texts.emplace_back(t);},[&](auto i){bool ok=real?game->respond(i):false;calls.push_back({2,(long long)i,ok});return ok;}};
  auto p=[](auto n){if constexpr(std::is_unsigned_v<decltype(n)>&&sizeof(n)==8)std::cout<<' '<<n;else std::cout<<' '<<static_cast<long long>(n);};auto h=[](auto n){std::cout<<' '<<n;};auto str=[&](std::string_view s){p(s.size());h(magic_digest(s));};
  auto movie=[&](const auto &m){p(bool(m));if(m){auto &d=m->decoder;p(d.width());p(d.height());p(d.frame_count());p(d.delay_ms());p(d.decoded_frames());p(d.cursor_);h(magic_digest(d.indices()));h(magic_digest(d.palette()));auto &im=m->image;p(im.width);p(im.height);p(im.origin_x);p(im.origin_y);p(im.pixels.size());h(magic_digest(im.pixels));p(im.opaque_pixels.size());h(magic_digest(im.opaque_pixels));p(m->sounded);}};
  auto decision=[&]()->const GameDecision&{if(real){if(!game->pending_decision())throw std::runtime_error("magic decision absent");return *game->pending_decision();}return fixture;};
  unsigned step=0;std::string line;
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;calls.clear();texts.clear();std::vector<std::uint8_t> old;std::uint32_t old_rng=0;if(op=='D'||op=='F'){old=game->world().export_save();old_rng=game->random_state();}
   if(op=='N'){
    unsigned m,ch;in>>m>>ch;NewGameOptions opt;opt.map_id=m%4;opt.stage_id=m/4;for(unsigned i=0;i<4;++i){opt.players[i].character=(ch+3*i)%12;opt.players[i].controller=1;}
    game=std::make_unique<GameSession>(World::from_map_resource(art.archive('m').decode(m*2+1),opt),1);screen.reset();buttons.clear();real=false;
   }else if(op=='W'){
    unsigned profile;in>>profile;auto &w=game->impl_->world;auto base=w.active_player().state;
    for(unsigned i=0;i<w.players.size();++i){auto &p=w.players[i];p.state.cash=1000+100*i;p.state.bank_balance=2000+100*i;p.state.points=100+10*i;p.state.sex=i%2;p.state.cards={};p.state.tool_amounts={};p.status.god_info=profile&&i==0?1:0;p.state.traffic_method=profile?i%3:0;p.state.dice_count=1+(p.state.traffic_method&3);p.state.x=base.x;p.state.y=base.y;p.state.node_id=base.node_id;p.state.last_node_id=base.last_node_id;if(profile){p.state.cards[0]=i+1;p.state.cards[1]=13;p.state.tool_amounts[0]=i+1;}}
    for(std::size_t i=1;i<w.lands.size();++i){w.lands[i].economy.owner_code=profile?1+i%4:0;w.lands[i].economy.level=profile?i%6:0;w.lands[i].economy.chain_store=0;}
    if(profile){w.objects[0].attached_player=1;w.objects[0].node_id=0;w.objects[0].remaining_days=5;}
   }else if(op=='O'){game->impl_->open_magic();if(!game->pending_decision()||game->pending_decision()->kind!=DecisionKind::magic_category)throw std::runtime_error("real magic not reached");real=true;}
   else if(op=='B'){
    int group,effect;std::uint64_t casting;in>>group>>effect>>casting;fixture={};fixture.kind=DecisionKind::magic_effect;fixture.player=0;for(int i=0;i<12;++i)fixture.options.push_back({"",i});fixture.options.push_back({"",-1});real=false;
    screen.magic_={};screen.magic_.active=true;screen.magic_.category=group;screen.magic_.selected=effect;screen.magic_.casting=casting;
   }else if(op=='T'){int group,effect;in>>group>>effect;screen.start_magic_cast(group,effect);}
   else if(op=='C'){long long t;in>>t;if(t<0)screen.clock.reset();else screen.clock=t;}
   else if(op=='U')screen.run_deferred();
   else if(op=='R'){screen.reset();buttons.clear();}
   else if(op=='E'){screen.end_visits();buttons.clear();}
   else if(op=='P'){in>>f.pointer_x>>f.pointer_y;}
   else if(op=='K'){unsigned value;in>>value;auto it=std::find(screen.magic_mask_.begin(),screen.magic_mask_.end(),value);if(it==screen.magic_mask_.end())throw std::runtime_error("magic mask value absent");auto i=std::size_t(it-screen.magic_mask_.begin());f.pointer_x=i%640;f.pointer_y=i/640;}
   else if(op=='D'||op=='F'){
    in>>f.ticks>>f.pointer_x>>f.pointer_y>>f.pointer_down;for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;buttons.clear();screen.shot.clear();
    if(op=='D')screen.draw_magic(f,*game,decision(),host);else screen.draw_magic_cast(f);
   }else if(op=='X'||op=='V'){
    int id;in>>id;if(op=='V'){auto &d=decision();auto it=std::find_if(d.options.begin(),d.options.end(),[&](auto &o){return o.value==id;});if(it==d.options.end())throw std::runtime_error("magic option absent");id=210+int(it-d.options.begin());}
    bool found=false;for(auto &b:buttons)if(b.id==id&&b.enabled){found=true;auto a=b.action;buttons.clear();a();break;}if(!found)throw std::runtime_error("expected magic button missing: "+std::to_string(id));
   }else return 3;
   auto &g=*game->impl_;auto dat=g.world.export_save();if(!old.empty()&&(old!=dat||old_rng!=game->random_state()))throw std::runtime_error("magic drawing changed world/RNG");
   std::cout<<-1;p(game->phase());p(game->random_state());p(bool(g.decision));if(g.decision){p(g.decision->kind);p(g.decision->options.size());for(auto &o:g.decision->options){str(o.label);p(o.value);}}p(g.magic_category);
   auto &m=screen.magic_;p(m.active);p(m.opened);p(m.category);p(m.selected);p(m.casting);p(m.scheduled);movie(m.movie);
   p(bool(screen.cast_));if(screen.cast_){auto &c=*screen.cast_;p(c.group);p(c.effect);p(c.started);movie(c.movie);}p(screen.deferred_.size());str(screen.voiced_);p(bool(screen.clock));if(screen.clock)p(*screen.clock);str(screen.shot);p(screen.magic_mask_.size());h(magic_digest(screen.magic_mask_));
   p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
   p(calls.size());for(auto &c:calls){p(c.size());for(auto n:c)p(n);}p(texts.size());for(auto &s:texts)str(s);p(dat.size());std::cout<<'\n';
   if(op=='D'||op=='F'){std::vector<char> raw;raw.reserve(canvas.pixels.size()*2);for(auto v:canvas.pixels){raw.push_back(char(v));raw.push_back(char(v>>8));}std::cout.write(raw.data(),raw.size());}std::cout.write(reinterpret_cast<const char*>(dat.data()),dat.size());std::cout.flush();++step;
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
