// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: actual original OptionsScreen/SaveLoadScreen with real art/font and captured actions.
#include "screens/menus.hpp"
#include <iostream>
#include <sstream>
int main(int argc,char **argv){
 if(argc!=3)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;using namespace native::screens;native::Artwork art(argv[1]);ui::Font font(argv[2]);
  auto canvas=graphics::make_canvas(640,480,0);std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);
  OptionsScreen options;SaveLoadScreen slots;std::array<SaveSlot,6> data{};unsigned caps=15,playing=0;
  std::vector<std::vector<long long>> calls;Host host{f,[&](auto n){calls.push_back({0,n});},{}};
  auto state=[](const OptionsState &s){return std::vector<long long>{s.speed,s.music,s.sound,s.animation};};
  auto actions=[&]{OptionsActions a;a.apply=[&](const auto &s){auto v=state(s);v.insert(v.begin(),1);calls.push_back(v);};a.close=[&]{calls.push_back({2,0});};if(caps&1)a.play_song=[&](auto n){calls.push_back({3,n});};a.playing_song=playing;if(caps&2)a.restart=[&]{calls.push_back({4,0});};if(caps&4)a.quit=[&]{calls.push_back({5,0});};if(caps&8)a.help=[&]{calls.push_back({6,0});};return a;};
  auto p=[](auto n){std::cout<<' '<<static_cast<long long>(n);};
  unsigned step=0;std::string line;
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;calls.clear();
   if(op=='O'){OptionsState s;bool ingame;in>>s.speed>>s.music>>s.sound>>s.animation>>ingame>>caps>>playing;options.open(s,ingame);}
   else if(op=='S'){
    unsigned slot,day,month,year,count;in>>slot;auto &s=data.at(slot);in>>s.valid>>day>>month>>year>>s.map>>s.stage>>count;
    s.date={static_cast<std::uint8_t>(day),static_cast<std::uint8_t>(month),static_cast<std::uint16_t>(year)};s.characters.clear();for(unsigned i=0;i<count;++i){unsigned c;in>>c;s.characters.push_back(c);}
   }else if(op=='L'){bool saving;in>>saving;slots.open(saving,data);}
   else if(op=='D'||op=='F'){
    in>>f.ticks>>f.pointer_x>>f.pointer_y>>f.pointer_down;for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;buttons.clear();
    if(op=='D')options.draw(host,actions());else slots.draw(host,[&](int n){calls.push_back({7,n});},[&]{calls.push_back({8,0});});
   }else if(op=='X'){int id;in>>id;for(auto &b:buttons)if(b.id==id&&b.enabled){auto a=b.action;buttons.clear();a();break;}}
   else return 3;
   std::cout<<-1;for(auto n:state(options.state_))p(n);p(options.in_game_);p(options.confirm_);p(slots.saving_);p(slots.hovered_);
   for(auto &s:slots.slots_){p(s.valid);p(s.date.day);p(s.date.month);p(s.date.year);p(s.map);p(s.stage);p(s.characters.size());for(auto c:s.characters)p(c);}
   p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
   p(calls.size());for(auto &c:calls){p(c.size());for(auto n:c)p(n);}std::cout<<'\n';
   if(op=='D'||op=='F'){std::vector<char> raw;raw.reserve(canvas.pixels.size()*2);for(auto v:canvas.pixels){raw.push_back(char(v));raw.push_back(char(v>>8));}std::cout.write(raw.data(),raw.size());}std::cout.flush();++step;
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
