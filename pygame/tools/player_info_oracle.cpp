// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: original PlayerInfo, real maps/art/font, no mutation on queries.
#include "screens/menus.hpp"
#include <iostream>
#include <sstream>
int main(int argc,char **argv){
 if(argc!=3)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;native::Artwork art(argv[1]);ui::Font font(argv[2]);World world;native::screens::PlayerInfo screen;
  auto canvas=graphics::make_canvas(640,480,0);std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);
  std::vector<std::pair<int,int>> calls;native::screens::Host host{f,[&](auto n){calls.emplace_back(0,n);},{}};
  auto p=[](auto n){std::cout<<' '<<static_cast<long long>(n);};unsigned step=0;std::string line;
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;calls.clear();std::vector<std::uint8_t> old;
   if(op=='D'||op=='X')old=world.export_save();
   if(op=='N'){
    unsigned map,ch;in>>map>>ch;NewGameOptions opt;opt.map_id=map%4;opt.stage_id=map/4;for(unsigned i=0;i<4;++i)opt.players[i].character=(ch+3*i)%12;
    world=World::from_map_resource(art.archive('m').decode(map*2+1),opt);screen={};buttons.clear();
   }else if(op=='V'){
    unsigned seed;in>>seed;world.header.price_index=1+seed%5;
    for(std::size_t i=0;i<world.lands.size();++i){auto &d=world.lands[i];d.economy.owner_code=1+i%4;d.economy.chain_store=i%3==0;d.economy.level=i%6;d.land_price=100+i*7;d.price_per_level=20+i;d.expired_date=i%2?(2030U<<16)|((1+i%12)<<8)|(1+i%28):0;}
    for(std::size_t i=0;i<world.facilities.size();++i){auto &d=world.facilities[i];d.owner_code=1+i%4;d.level=i%6;d.land_price=300+i;d.expired_date=(2035U<<16)|(12<<8)|31;}
    for(auto &c:world.commercials)c.owner_code=1+c.id%4;
    for(std::size_t i=0;i<world.players.size();++i){auto &p=world.players[i];p.state.cash=12345+1000*i;p.state.bank_balance=56789-1111*i;p.state.loan=100*i;p.status.days_assurance=20+i;
     for(unsigned t=0;t<p.state.tool_amounts.size();++t)p.state.tool_amounts[t]=(t+i+seed)%4;
     for(unsigned k=0;k<p.state.cards.size();++k)p.state.cards[k]=(k*3+i+seed)%33;
     for(unsigned s=0;s<12;++s){p.stocks[s].amount=(s+i+seed)%4?(s+1)*100:0;p.stocks[s].raw_cost_basis=0x41200000;}
    }
   }else if(op=='G'){
    unsigned slot,info,kind,days;in>>slot>>info>>kind>>days;world.players.at(slot).status.god_info=info;
    if(info&&info<=world.objects.size()){world.objects[info-1].kind=kind;world.objects[info-1].remaining_days=days;}
   }else if(op=='O'){unsigned player;in>>player;screen.open(player);}
   else if(op=='S'){in>>screen.page_>>screen.category_>>screen.scroll_;}
   else if(op=='D'){
    in>>f.ticks>>f.pointer_x>>f.pointer_y>>f.pointer_down;for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;buttons.clear();screen.draw(host,world,[&]{calls.emplace_back(1,0);});
   }else if(op=='X'){int id;in>>id;for(auto &b:buttons)if(b.id==id&&b.enabled){auto a=b.action;buttons.clear();a();break;}}
   else return 3;
   if(!old.empty()&&old!=world.export_save())throw std::runtime_error("PlayerInfo changed World DAT");
   std::cout<<-1;p(screen.player_);p(screen.page_);p(screen.category_);p(screen.scroll_);
   p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
   p(calls.size());for(auto [a,b]:calls){p(a);p(b);}std::cout<<'\n';
   if(op=='D'){std::vector<char> raw;raw.reserve(canvas.pixels.size()*2);for(auto v:canvas.pixels){raw.push_back(char(v));raw.push_back(char(v>>8));}std::cout.write(raw.data(),raw.size());}std::cout.flush();++step;
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
