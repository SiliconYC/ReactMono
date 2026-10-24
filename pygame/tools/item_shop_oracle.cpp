// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: pinned original Shop screens + private visit entry, public real respond, complete World DAT.
#include "game.cpp"
#include "screens/items.cpp"
#include <sstream>
#include <type_traits>
extern "C" std::uint64_t SDL_GetTicks(){return 0;}
int main(int argc,char **argv){
 if(argc!=3)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;using namespace native::items;native::Artwork art(argv[1]);ui::Font font(argv[2]);
  auto canvas=graphics::make_canvas(640,480,0);std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);Screens screen;std::unique_ptr<GameSession> game;
  std::vector<std::vector<long long>> calls;std::vector<std::string> texts;
  screen.sound=[&](auto n){calls.push_back({0,(long long)n});};screen.speech=[&](auto n,bool q){calls.push_back({1,(long long)n,q});};
  Host host{[&]{calls.push_back({4});},[&](bool ok,std::string_view t){calls.push_back({3,ok});texts.emplace_back(t);},[&](auto i){bool ok=game->respond(i);calls.push_back({2,(long long)i,ok});return ok;}};
  auto p=[](auto n){if constexpr(std::is_unsigned_v<decltype(n)>&&sizeof(n)==8)std::cout<<' '<<n;else std::cout<<' '<<static_cast<long long>(n);};auto str=[&](std::string_view s){std::uint64_t h=14695981039346656037ULL;for(unsigned char c:s){h^=c;h*=1099511628211ULL;}p(s.size());std::cout<<' '<<h;};
  unsigned step=0;std::string line;
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;calls.clear();texts.clear();int result=-1;std::vector<std::uint8_t> old;std::uint32_t old_rng=0;
   if(op=='D'){old=game->world().export_save();old_rng=game->random_state();}
   if(op=='N'){
    unsigned m,ch;in>>m>>ch;NewGameOptions opt;opt.map_id=m%4;opt.stage_id=m/4;for(unsigned i=0;i<4;++i){opt.players[i].character=(ch+3*i)%12;opt.players[i].controller=1;}
    game=std::make_unique<GameSession>(World::from_map_resource(art.archive('m').decode(m*2+1),opt),1);screen.reset();buttons.clear();
   }else if(op=='W'){
    unsigned points,profile,amount,owner;int cards,tools;in>>points>>profile>>cards>>tools>>amount>>owner;auto &w=game->impl_->world;auto &p=w.active_player().state;
    p.points=points;p.cards={};p.tool_amounts={};if(profile){for(unsigned j=0;j<15;++j)p.cards[j]=1+j+(profile==2?15:0);for(unsigned j=0;j<13;++j)p.tool_amounts[j]=profile==2?9:1+j%3;}
    if(profile==3)p.cards={1,0,14,14,18,0,30,0,20,2,0,15,0,9,8};
    w.card_supply={};for(unsigned j=0;j<30;++j)if(cards==-1||cards==int(j+1))w.card_supply[j]=amount;
    w.tool_supply={};for(unsigned j=0;j<8;++j)if(tools==-1||tools==int(j+1))w.tool_supply[j]=amount;
    for(auto &c:w.commercials)c.owner_code=owner;
   }else if(op=='O'){
    auto &g=*game->impl_;auto it=std::find_if(g.world.nodes.begin(),g.world.nodes.end(),[](auto &n){return (n.flags&255)==15;});if(it==g.world.nodes.end())throw std::runtime_error("map has no actual shop node");g.open_shop(it->type_and_index);
    if(!game->pending_decision()||game->pending_decision()->kind!=DecisionKind::shop)throw std::runtime_error("actual shop not reached");
   }else if(op=='S'){int value;in>>value;result=screen.shop_show_option(value);}
   else if(op=='C'){long long t;in>>t;if(t<0)screen.clock.reset();else screen.clock=t;}
   else if(op=='U')screen.run_deferred();
   else if(op=='R'){screen.reset();buttons.clear();}
   else if(op=='F'){screen.end_visits();buttons.clear();}
   else if(op=='D'){
    in>>f.ticks>>f.pointer_x>>f.pointer_y>>f.pointer_down;for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;buttons.clear();screen.shot.clear();
    if(!game->pending_decision()||game->pending_decision()->kind!=DecisionKind::shop)throw std::runtime_error("shop draw without real shop decision");screen.draw_shop(f,*game,*game->pending_decision(),host);
   }else if(op=='X'||op=='V'){
    int id;in>>id;if(op=='V'){if(!game->pending_decision())throw std::runtime_error("no real shop decision");auto &d=*game->pending_decision();auto it=std::find_if(d.options.begin(),d.options.end(),[&](auto &o){return o.value==id;});if(it==d.options.end())throw std::runtime_error("real shop value missing");id=210+int(it-d.options.begin());}
    bool found=false;for(auto &b:buttons)if(b.id==id&&b.enabled){found=true;auto a=b.action;buttons.clear();a();break;}if(!found)throw std::runtime_error("expected shop button missing: "+std::to_string(id));
   }else return 3;
   auto &g=*game->impl_;auto dat=g.world.export_save();if(!old.empty()&&(old!=dat||old_rng!=game->random_state()))throw std::runtime_error("shop draw changed world/RNG");
   std::cout<<result;p(game->phase());p(game->random_state());p(bool(g.decision));if(g.decision){p(g.decision->kind);p(g.decision->options.size());for(auto &o:g.decision->options){str(o.label);p(o.value);}}
   p(bool(g.shop));if(g.shop){auto &s=*g.shop;p(s.cards.size());for(auto n:s.cards)p(n);p(s.tools.size());for(auto n:s.tools)p(n);p(s.revenue);p(s.gift_card);p(s.gift_tool);p(s.closed);}p(g.shop_property);
   auto &s=screen.shop_;p(s.active);p(s.mode);p(s.cards.size());for(auto n:s.cards)p(n);p(s.tools.size());for(auto n:s.tools)p(n);p(s.cards_bought.size());for(auto n:s.cards_bought)p(n);p(s.tools_bought.size());for(auto n:s.tools_bought)p(n);
   p(s.opened);p(s.balloon_until);str(s.balloon);p(s.leaving);p(s.leave_at);p(s.pick_kind);p(s.pick_index);p(s.pick_value);p(bool(screen.shop_pending_value()));if(screen.shop_pending_value())p(*screen.shop_pending_value());
   p(screen.deferred_.size());str(screen.voiced_);p(bool(screen.clock));if(screen.clock)p(*screen.clock);str(screen.shot);p(screen.descriptions_.size());for(auto &[k,v]:screen.descriptions_){p(k.first);p(k.second);str(v);}
   p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
   p(calls.size());for(auto &c:calls){p(c.size());for(auto n:c)p(n);}p(texts.size());for(auto &s:texts)str(s);p(dat.size());std::cout<<'\n';
   if(op=='D'){std::vector<char> raw;raw.reserve(canvas.pixels.size()*2);for(auto v:canvas.pixels){raw.push_back(char(v));raw.push_back(char(v>>8));}std::cout.write(raw.data(),raw.size());}std::cout.write(reinterpret_cast<const char*>(dat.data()),dat.size());std::cout.flush();++step;
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
