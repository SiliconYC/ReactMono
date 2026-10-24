// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: original target/dice/steal/frame-up components; explicit gallery states plus actual core paths.
#include "screens/items.cpp"
#include <sstream>
extern "C" std::uint64_t SDL_GetTicks(){return 0;}
int main(int argc,char **argv){
 if(argc!=3)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;using namespace native::items;native::Artwork art(argv[1]);ui::Font font(argv[2]);
  auto canvas=graphics::make_canvas(640,480,0);std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);
  Screens screen;std::unique_ptr<GameSession> game;GameDecision decision;board::Camera camera{{16,16},0,{0,40,440,480}};bool real=false;
  std::vector<std::vector<long long>> calls;screen.sound=[&](auto n){calls.push_back({0,(long long)n});};
  Host host{[&]{calls.push_back({3});},[&](bool ok,std::string_view){calls.push_back({4,ok});},[&](auto i){bool ok=real?game->respond(i):false;calls.push_back({1,(long long)i,ok});return ok;}};
  auto p=[](auto n){std::cout<<' '<<static_cast<long long>(n);};auto str=[&](std::string_view s){std::uint64_t h=14695981039346656037ULL;for(unsigned char c:s){h^=c;h*=1099511628211ULL;}p(s.size());std::cout<<' '<<h;};
  unsigned step=0;std::string line;
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;calls.clear();std::vector<std::uint8_t> old;if(op=='D')old=game->world().export_save();
   if(op=='N'){
    unsigned m,ch;in>>m>>ch;NewGameOptions opt;opt.map_id=m%4;opt.stage_id=m/4;for(unsigned i=0;i<4;++i){opt.players[i].character=(ch+3*i)%12;opt.players[i].controller=1;}
    game=std::make_unique<GameSession>(World::from_map_resource(art.archive('m').decode(m*2+1),opt),1);screen.reset();buttons.clear();real=false;
   }else if(op=='W'){
    unsigned profile;in>>profile;auto &w=const_cast<World&>(game->world());auto &p=w.players[1].state;p.cards={};p.tool_amounts={};
    if(profile){for(unsigned j=0;j<15;++j)p.cards[j]=1+j+(profile==2?15:0);for(unsigned j=0;j<13;++j)p.tool_amounts[j]=1+j%9;}
    if(profile==3)p.cards={0,1,14,14,18,30,0,0,20,2,0,15,0,9,8};
   }else if(op=='M'){unsigned rotation;in>>camera.center.x>>camera.center.y>>rotation;camera.rotation=rotation;}
   else if(op=='B'){
    int type,n,cancel;in>>type>>n>>cancel;decision={};decision.player=0;real=false;
    if(type==0){decision.kind=DecisionKind::action_target;for(int v=1;v<=6;++v)decision.options.push_back({"",v});if(cancel)decision.options.push_back({"",0});}
    else if(type==1){decision.kind=DecisionKind::action_target;decision.victim=1;if(n){auto &p=game->world().players[1].state;for(unsigned id=1;id<=30;++id)if(std::find(p.cards.begin(),p.cards.end(),id)!=p.cards.end())decision.options.push_back({"",int((unsigned(CardTargetKind::card)<<16)|id)});for(unsigned id=1;id<=13;++id)if(p.tool_amounts[id-1])decision.options.push_back({"",int((unsigned(CardTargetKind::tool)<<16)|id)});}if(cancel)decision.options.push_back({"",-1});}
    else if(type==2){decision.kind=DecisionKind::card_target;for(int i=0;i<n&&i<4;++i)decision.options.push_back({"",i});if(cancel)decision.options.push_back({"",-1});}
    else if(type==3){decision.kind=DecisionKind::action_target;screen.last_tool_=n;decision.prompt="";if(cancel>0&&cancel<=30)decision.prompt=std::string(services::card_names[cancel-1]);else if(cancel==31)decision.prompt="目的";
     constexpr std::pair<int,int> offsets[]={{-480,0},{-448,0},{-400,0},{-64,0},{-32,0},{-16,0},{0,0},{1,0},{16,0},{32,0},{64,0},{400,0},{448,0},{480,0},{0,-400},{0,400},{320,320},{-320,-320}};
     int i=0;for(auto [x,y]:offsets)decision.options.push_back({"",i++,DecisionLocation{camera.center.x+x,camera.center.y+y}});decision.options.push_back({"",-1});
    }else return 4;
   }else if(op=='A'){
    int kind;in>>kind;auto &p=const_cast<World&>(game->world()).active_player().state;p.cards={};p.tool_amounts={};bool ok=false;
    if(kind==0){p.tool_amounts[7]=1;ok=game->use_tool(8);}else{auto &victim=const_cast<World&>(game->world()).players[1].state;victim.x=p.x;victim.y=p.y;victim.node_id=p.node_id;victim.last_node_id=p.last_node_id;p.cards[0]=13;ok=game->use_card({13,CardTarget{CardTargetKind::actor,1},{}});}
    if(!ok||!game->pending_decision())throw std::runtime_error("actual item decision not reached");decision=*game->pending_decision();real=true;
   }else if(op=='C'){long long t;in>>t;if(t<0)screen.clock.reset();else screen.clock=t;}
   else if(op=='R'){screen.reset();buttons.clear();}
   else if(op=='V'){in>>f.pointer_x>>f.pointer_y;}
   else if(op=='D'){
    int type,selected;in>>type>>f.ticks>>f.pointer_x>>f.pointer_y>>f.pointer_down>>selected;
    for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;buttons.clear();screen.shot.clear();
    if(type==0)screen.draw_remote_dice(f,decision,host);else if(type==1)screen.draw_steal(f,*game,decision,host);else if(type==2)screen.draw_frame_up(f,*game,decision,host);
    else screen.draw_targets(f,decision,camera,selected<0?std::optional<std::size_t>{}:std::optional<std::size_t>(selected),[&](auto i){calls.push_back({2,(long long)i});});
   }else if(op=='X'){int id;in>>id;bool found=false;for(auto &b:buttons)if(b.id==id&&b.enabled){found=true;auto a=b.action;buttons.clear();a();break;}if(!found)throw std::runtime_error("expected target button missing: "+std::to_string(id));}
   else return 3;
   auto dat=game->world().export_save();if(!old.empty()&&old!=dat)throw std::runtime_error("target draw changed World DAT");
   std::cout<<-1;p(game->phase());p(game->random_state());p(bool(game->pending_decision()));if(game->pending_decision()){p(game->pending_decision()->kind);p(game->pending_decision()->options.size());}
   p(bool(screen.steal_pick_));if(screen.steal_pick_)p(*screen.steal_pick_);p(screen.last_tool_);p(bool(screen.clock));if(screen.clock)p(*screen.clock);str(screen.shot);
   p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
   p(calls.size());for(auto &c:calls){p(c.size());for(auto n:c)p(n);}p(dat.size());std::cout<<'\n';
   if(op=='D'){std::vector<char> raw;raw.reserve(canvas.pixels.size()*2);for(auto v:canvas.pixels){raw.push_back(char(v));raw.push_back(char(v>>8));}std::cout.write(raw.data(),raw.size());}std::cout.write(reinterpret_cast<const char*>(dat.data()),dat.size());std::cout.flush();++step;
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
