// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: actual original MainMenu/NewGameSetup and raw mt19937, real artwork/font.
#include "screens/menus.hpp"
#include <iostream>
#include <sstream>
int main(int argc,char **argv){
 if(argc!=3)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;using namespace native::screens;native::Artwork art(argv[1]);ui::Font font(argv[2]);
  auto canvas=graphics::make_canvas(640,480,0);std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);
  MainMenu menu;NewGameSetup setup;std::vector<std::vector<long long>> calls;
  Host host{f,[&](auto n){calls.push_back({0,n});},{}};
  MenuActions actions{[&]{calls.push_back({1,1});},[&]{calls.push_back({1,2});},[&]{calls.push_back({1,3});},[&]{calls.push_back({1,5});},[&]{calls.push_back({1,4});},true};
  auto choice=[](const NewGameChoice &c){std::vector<long long> v{2,c.stage,c.map,c.fund,c.lease_mode,static_cast<long long>(c.players.size())};for(auto &p:c.players){v.push_back(p.character);v.push_back(p.controller);v.push_back(p.traffic_method);v.push_back(p.start_node);}return v;};
  auto start=[&](const NewGameChoice &c){calls.push_back(choice(c));};auto close=[&]{calls.push_back({3,0});};
  auto p=[](auto n){std::cout<<' '<<static_cast<long long>(n);};
  unsigned step=0;std::string line;
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;calls.clear();
   if(op=='O'){unsigned stage,map,seed;in>>stage>>map>>seed;setup.open(stage,map,seed);}
   else if(op=='R')menu={};
   else if(op=='V')for(auto &v:setup.values_)in>>v;
   else if(op=='G')setup.fill_one();
   else if(op=='Q')calls.push_back(choice(setup.choice()));
   else if(op=='D'||op=='M'){
    in>>f.ticks>>f.pointer_x>>f.pointer_y>>f.pointer_down;bool flag;in>>flag;
    for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;buttons.clear();
    if(op=='M'){actions.load_enabled=flag;menu.draw(host,actions);}else{host.instant=flag;setup.draw(host,start,close);}
   }else if(op=='X'){int id;in>>id;for(auto &b:buttons)if(b.id==id&&b.enabled){auto a=b.action;buttons.clear();a();break;}}
   else if(op=='B')setup.cancel(host,close);
   else return 3;
   std::cout<<-1;p(menu.hovered_);p(setup.stage_);p(setup.map_);for(auto n:setup.values_)p(n);
   p(setup.picks_.size());for(auto n:setup.picks_)p(n);p(setup.human_count_);p(setup.dropdown_);p(setup.hovered_);p(setup.filling_);p(setup.leaving_);p(setup.fill_tick_);p(setup.leave_tick_);p(setup.backdrop_key_);p(setup.backdrop_.width);p(setup.backdrop_.height);
   std::ostringstream rs;rs<<setup.random_;std::istringstream rin(rs.str());std::vector<std::uint32_t> state;std::uint32_t n;while(rin>>n)state.push_back(n);p(state.size());for(auto v:state)p(v);
   p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
   p(calls.size());for(auto &c:calls){p(c.size());for(auto v:c)p(v);}std::cout<<'\n';
   if(op=='D'||op=='M'){std::vector<char> raw;raw.reserve(canvas.pixels.size()*2);for(auto v:canvas.pixels){raw.push_back(char(v));raw.push_back(char(v>>8));}std::cout.write(raw.data(),raw.size());}std::cout.flush();++step;
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
