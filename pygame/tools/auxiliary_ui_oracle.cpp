// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: direct original HelpScreen and tile_popup, real external archives/fonts/maps.
#include "screens/help.cpp"
#include "screens/tile_popup.cpp"
#include <iostream>
#include <sstream>
extern "C" std::uint64_t SDL_GetTicks(){return 0;}
int main(int argc,char **argv){
 if(argc!=3)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;native::Artwork art(argv[1]);ui::Font font(argv[2]);World world;native::screens::HelpScreen screen;
  auto canvas=graphics::make_canvas(640,480);std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);
  std::vector<int> calls;native::screens::Host host{f,[&](int n){calls.push_back(n);},{}};
  auto p=[](auto n){std::cout<<' '<<static_cast<long long>(n);};
  auto text=[&](const std::string &s){std::uint64_t h=14695981039346656037ULL;for(unsigned char c:s)h=(h^c)*1099511628211ULL;p(s.size());std::cout<<' '<<h;};
  std::string line;std::size_t step=0;
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;calls.clear();int result=-1;std::vector<native::tile_popup::Line> lines;
   auto old=world.nodes.empty()?std::vector<std::uint8_t>{}:world.export_save();
   if(op=='N'){
    unsigned m,ch;in>>m>>ch;NewGameOptions opt;opt.map_id=m%4;opt.stage_id=m/4;for(unsigned i=0;i<4;++i){opt.players[i].character=(ch+3*i)%12;opt.players[i].controller=1;}
    world=World::from_map_resource(art.archive('m').decode(2*m+1),opt);screen={};buttons.clear();
   }else if(op=='V'){
    unsigned seed;in>>seed;world.header.price_index=1+seed%5;
    for(std::size_t i=1;i<world.lands.size();++i){auto &d=world.lands[i].economy;d.owner_code=(i+seed)%6;d.chain_store=(i+seed)%3==0;d.level=(i+seed)%6;}
    for(std::size_t i=1;i<world.facilities.size();++i){auto &d=world.facilities[i];d.owner_code=(i+seed)%6;d.facility_type=(i+seed)%6;d.level=(i+seed)%6;}
    for(std::size_t i=1;i<world.commercials.size();++i){auto &d=world.commercials[i];d.owner_code=(i+seed)%6;d.shares_remaining=seed*127+i;}
    const auto &n=world.nodes.at(1+seed%(world.nodes.size()-1));
    for(unsigned i=0;i<world.players.size();++i){auto &p=world.players[i];p.state.x=n.x+8*i;p.state.y=n.y+4*i;p.state.controller_flags=i==3?0:1;p.status.days_disappearing=i==2?1:0;}
    for(unsigned i=0;i<4;++i){auto &a=world.special_actors[i];a.x=n.x+6*i;a.y=n.y+3*i;a.node_id=n.id;a.inactive_state=i==2;}
    for(std::size_t i=0;i<world.objects.size();++i){auto &o=world.objects[i];o.kind=1+(i+seed)%20;o.node_id=i%5?1+(i+seed)%(world.nodes.size()-1):0;o.attached_player=i%7==0;}
   }else if(op=='O'){int x,y;in>>x>>y;screen.open(x,y);}
   else if(op=='A'){unsigned c,t;in>>c>>t;screen.select(art,c,t);}
   else if(op=='J'){int d;in>>d;screen.scroll(d);}
   else if(op=='C')screen.close();
   else if(op=='E')screen.cancel(host);
   else if(op=='P'){board::Camera camera;int x,y;unsigned rotation;in>>camera.center.x>>camera.center.y>>rotation>>x>>y;camera.rotation=std::uint8_t(rotation);result=native::tile_popup::instance_at(world,camera,x,y);}
   else if(op=='L'){unsigned code;in>>code;lines=native::tile_popup::lines(world,std::uint16_t(code));}
   else if(op=='D'||op=='T'){
    for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;buttons.clear();
    if(op=='D'){in>>f.ticks>>f.pointer_x>>f.pointer_y>>f.pointer_down;screen.draw(host);}
    else{unsigned code;int x,y;in>>code>>x>>y;native::tile_popup::Popup pop{x,y,std::uint16_t(code)};lines=native::tile_popup::lines(world,pop.code);native::tile_popup::draw(f,world,pop);}
   }else if(op=='X'){
    int id;in>>id;bool found=false;for(auto &b:buttons)if(b.id==id&&b.enabled){auto a=b.action;buttons.clear();a();found=true;break;}if(!found)throw std::runtime_error("expected help button absent");
   }else return 3;
   const auto dat=world.export_save();if(op!='N'&&op!='V'&&old!=dat)throw std::runtime_error("auxiliary UI changed World DAT");
   std::cout<<result;p(lines.size());for(const auto &l:lines){p(l.dy);text(l.text);}
   p(screen.open_);p(screen.x_);p(screen.y_);p(screen.category_);p(screen.topic_);for(auto n:screen.first_)p(n);p(screen.page_);p(screen.loaded_);p(screen.pages_.size());
   for(const auto &page:screen.pages_){p(page.size());for(const auto &s:page)text(s);}
   p(buttons.size());for(const auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
   p(calls.size());for(auto n:calls)p(n);p(dat.size());std::cout<<'\n';
   if(op=='D'||op=='T'){for(auto v:canvas.pixels){std::cout.put(char(v));std::cout.put(char(v>>8));}}std::cout.write(reinterpret_cast<const char*>(dat.data()),dat.size());std::cout.flush();++step;
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
