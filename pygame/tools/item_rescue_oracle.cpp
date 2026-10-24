// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: original rescue screens and complete item dispatcher, real confinement/visit/respond paths.
#include "game.cpp"
#include "screens/items.cpp"
#include <sstream>
#include <type_traits>
extern "C" std::uint64_t SDL_GetTicks(){return 0;}
int main(int argc,char **argv){
 if(argc!=3)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;using namespace native::items;native::Artwork art(argv[1]);ui::Font font(argv[2]);
  auto canvas=graphics::make_canvas(640,480,0);std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);Screens screen;std::unique_ptr<GameSession> game;bool hospital=false,real=true;
  std::vector<std::vector<long long>> calls;std::vector<std::string> texts;screen.sound=[&](auto n){calls.push_back({0,(long long)n});};screen.speech=[&](auto n,bool q){calls.push_back({1,(long long)n,q});};
  Host host{[&]{calls.push_back({4});},[&](bool ok,std::string_view t){calls.push_back({3,ok});texts.emplace_back(t);},[&](auto i){bool ok=real?game->respond(i):false;calls.push_back({2,(long long)i,ok});return ok;}};
  auto p=[](auto n){if constexpr(std::is_unsigned_v<decltype(n)>&&sizeof(n)==8)std::cout<<' '<<n;else std::cout<<' '<<static_cast<long long>(n);};auto str=[&](std::string_view s){std::uint64_t h=14695981039346656037ULL;for(unsigned char c:s){h^=c;h*=1099511628211ULL;}p(s.size());std::cout<<' '<<h;};
  unsigned step=0;std::string line;
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;calls.clear();texts.clear();int result=-1;std::vector<std::uint8_t> old;std::uint32_t old_rng=0;if(op=='D'){old=game->world().export_save();old_rng=game->random_state();}
   if(op=='N'){
    unsigned m,ch;in>>m>>ch;NewGameOptions opt;opt.map_id=m%4;opt.stage_id=m/4;for(unsigned i=0;i<4;++i){opt.players[i].character=(ch+3*i)%12;opt.players[i].controller=1;}
    game=std::make_unique<GameSession>(World::from_map_resource(art.archive('m').decode(m*2+1),opt),1);screen.reset();buttons.clear();hospital=false;real=true;
   }else if(op=='W'){
    unsigned points,mask,visitor;in>>hospital>>points>>mask>>visitor;if(mask&(1U<<visitor))throw std::runtime_error("visitor is in confinement fixture");auto &g=*game->impl_;g.world.header.current_player=visitor;
    auto &p=g.world.active_player().state;p.points=points;auto it=std::find_if(g.world.nodes.begin()+1,g.world.nodes.end(),[&](auto &n){return (n.flags&255)==(hospital?5U:4U);});if(it==g.world.nodes.end())throw std::runtime_error("map has no real confinement exit");g.world.nodes.at(p.node_id).flags&=~(0x100U<<visitor);p.node_id=it-g.world.nodes.begin();p.last_node_id=0;p.x=it->x;p.y=it->y;it->flags|=0x100U<<visitor;
    for(unsigned i=0;i<8;++i)if(mask&(1U<<i))g.add_confinement(i,3,hospital);
   }else if(op=='O'){auto &g=*game->impl_;g.visit_confinement(hospital);if(game->pending_decision()&&game->pending_decision()->kind!=DecisionKind::rescue)throw std::runtime_error("wrong actual rescue decision");real=true;}
   else if(op=='B'){
    unsigned kind,shape;in>>kind>>shape;GameDecision d{};d.kind=DecisionKind(kind);d.player=game->world().header.current_player;
    if(kind==unsigned(DecisionKind::shop))d.options={{"",101},{"",201},{"",0}};
    else if(kind==unsigned(DecisionKind::magic_category))for(int n:{0,3,6,9,11})d.options.push_back({"",n});
    else if(kind==unsigned(DecisionKind::magic_effect)){for(int i=0;i<12;++i)d.options.push_back({"",i});d.options.push_back({"",-1});}
    else if(kind==unsigned(DecisionKind::rescue)){d.prompt="探望住院角色";for(int i=0;i<8;++i)d.options.push_back({"",i});d.options.push_back({"",-1});}
    else if(kind==unsigned(DecisionKind::action_target)){
     if(shape==1||shape==3){for(int i=1;i<=6;++i)d.options.push_back({"",i});d.options.push_back({"",0});if(shape==3)d.options[0].location=DecisionLocation{1,2};}
     if(shape==2){d.victim=0;d.options={{"",(int(CardTargetKind::card)<<16)|1},{"",-1}};game->impl_->world.players[0].state.cards[0]=1;}
    }else if(kind==unsigned(DecisionKind::card_target)){
     d.prompt=shape==1?"請選擇嫁禍對象...":shape==2?"使用嫁祸卡？":shape==3?"是否嫁禍給某人？":"other";d.options={{"",1}};if(shape==1)d.options.push_back({"",2});d.options.push_back({"",-1});
    }
    game->impl_->decision=d;game->impl_->phase=GamePhase::awaiting_decision;real=false;
   }else if(op=='Z'){
    screen.shop_.active=true;screen.shop_.mode=1;screen.magic_.active=true;screen.magic_.category=7;screen.magic_.selected=-1;screen.rescue_.active=true;screen.rescue_.selected=-1;screen.voiced_="seed";screen.steal_pick_=0;
   }else if(op=='C'){long long t;in>>t;if(t<0)screen.clock.reset();else screen.clock=t;}
   else if(op=='U')screen.run_deferred();
   else if(op=='R'){screen.reset();buttons.clear();}
   else if(op=='E'){screen.end_visits();buttons.clear();}
   else if(op=='D'){
    bool dispatch;in>>f.ticks>>f.pointer_x>>f.pointer_y>>f.pointer_down>>dispatch;for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;buttons.clear();screen.shot.clear();
    if(!game->pending_decision())throw std::runtime_error("draw without pending decision");if(dispatch)result=screen.draw_decision(f,*game,host);else screen.draw_rescue(f,*game,*game->pending_decision(),host);
   }else if(op=='X'||op=='V'){
    int id;in>>id;if(op=='V'){if(!game->pending_decision())throw std::runtime_error("no pending rescue");auto &d=*game->pending_decision();auto it=std::find_if(d.options.begin(),d.options.end(),[&](auto &o){return o.value==id;});if(it==d.options.end())throw std::runtime_error("rescue value absent");id=210+int(it-d.options.begin());}
    bool found=false;for(auto &b:buttons)if(b.id==id&&b.enabled){found=true;auto a=b.action;buttons.clear();a();break;}if(!found)throw std::runtime_error("expected rescue button missing: "+std::to_string(id));
   }else return 3;
   auto &g=*game->impl_;auto dat=g.world.export_save();if(!old.empty()&&(old!=dat||old_rng!=game->random_state()))throw std::runtime_error("item dispatcher draw changed world/RNG");
   std::cout<<result;p(game->phase());p(game->random_state());p(bool(g.decision));if(g.decision){p(g.decision->kind);p(g.decision->options.size());for(auto &o:g.decision->options){str(o.label);p(o.value);}}p(g.rescue_hospital);
   auto &r=screen.rescue_;p(r.active);p(r.selected);p(r.poor_until);p(r.opened);p(r.thanks);p(r.thanks_until);p(r.thanks_scheduled);
   p(screen.shop_.active);p(screen.shop_.mode);p(screen.magic_.active);p(screen.magic_.category);p(screen.magic_.selected);p(screen.magic_.casting);p(screen.magic_.scheduled);p(bool(screen.magic_.movie));p(bool(screen.cast_));p(screen.deferred_.size());p(screen.popups_.size());p(bool(screen.steal_pick_));if(screen.steal_pick_)p(*screen.steal_pick_);
   str(screen.voiced_);p(bool(screen.clock));if(screen.clock)p(*screen.clock);str(screen.shot);
   p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
   p(calls.size());for(auto &c:calls){p(c.size());for(auto n:c)p(n);}p(texts.size());for(auto &s:texts)str(s);p(dat.size());std::cout<<'\n';
   if(op=='D'){std::vector<char> raw;raw.reserve(canvas.pixels.size()*2);for(auto v:canvas.pixels){raw.push_back(char(v));raw.push_back(char(v>>8));}std::cout.write(raw.data(),raw.size());}std::cout.write(reinterpret_cast<const char*>(dat.data()),dat.size());std::cout.flush();++step;
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
