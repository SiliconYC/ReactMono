// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: original StockMarket, real assets/font, explicit UI inputs and captured actions.
#include "screens/finance.hpp"
#include "rich4/calendar.hpp"
#include <bit>
#include <iostream>
#include <sstream>
int main(int argc,char **argv){
 if(argc!=3)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;using namespace native::screens;native::Artwork art(argv[1]);ui::Font font(argv[2]);World world;
  auto canvas=graphics::make_canvas(640,480,0);std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);
  StockMarket screen;NumberPad pad;GameDecision decision;unsigned player=0;bool accepted=true;
  std::vector<std::array<long long,3>> calls;Host host{f,[&](auto n){calls.push_back({0,n,0});},{}};
  StockActions actions{[&](auto s,auto n){calls.push_back({1,static_cast<long long>(s),n});return accepted;},[&](auto s,auto n){calls.push_back({2,static_cast<long long>(s),n});return accepted;},[&]{calls.push_back({3,0,0});}};
  auto respond=[&](auto n){calls.push_back({4,static_cast<long long>(n),0});};
  auto p=[](auto n){std::cout<<' '<<static_cast<long long>(n);};
  auto s=[&](const std::string &str){std::uint64_t h=14695981039346656037ULL;for(unsigned char c:str){h^=c;h*=1099511628211ULL;}p(str.size());std::cout<<' '<<h;};
  unsigned step=0;std::string line;
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;calls.clear();int result=-1;std::vector<std::uint8_t> old;
   if(op=='D'||op=='G'||op=='X'||op=='K'||op=='B')old=world.export_save();
   if(op=='N'){
    unsigned map,ch;in>>map>>ch>>player;NewGameOptions opt;opt.map_id=map%4;opt.stage_id=map/4;for(unsigned i=0;i<4;++i)opt.players[i].character=(ch+3*i)%12;
    world=World::from_map_resource(art.archive('m').decode(map*2+1),opt);screen.reset();pad=NumberPad{};buttons.clear();accepted=true;decision={};decision.kind=DecisionKind::card_target;
   }else if(op=='T'){
    unsigned d,m,y;in>>d>>m>>y>>world.news_effect_days;world.header.date={static_cast<std::uint8_t>(d),static_cast<std::uint8_t>(m),static_cast<std::uint16_t>(y)};
   }else if(op=='S'){int sel,pg;bool info;in>>sel>>pg>>info;screen.selected=sel<0?std::nullopt:std::optional<std::size_t>(sel);screen.page=pg;screen.info_open=info;}
   else if(op=='W'){unsigned slot;in>>slot>>world.players.at(slot).state.bank_balance;}
   else if(op=='P'){
    unsigned stock,listed,halt;in>>stock;auto &q=world.stocks.at(stock);in>>q.float_bits[2]>>q.float_bits[1]>>q.flags_10>>listed>>halt;q.flags_4=listed;q.suspension_days=halt;
   }else if(op=='V'){
    unsigned slot,stock;in>>slot>>stock;auto &h=world.players.at(slot).stocks.at(stock);in>>h.amount>>h.raw_cost_basis;
   }else if(op=='H'){
    unsigned stock,count,bits,stride;in>>stock>>world.stock_history_cursor>>count>>bits>>stride;auto &ring=world.stock_history_bits.at(stock);ring.fill(0);for(unsigned i=0;i<std::min(count,144U);++i)ring[i]=bits+stride*i;
   }else if(op=='C'){
    unsigned index,owner,type,stock;in>>index;auto &c=world.commercials.at(index);in>>owner>>type>>stock>>c.funds>>c.funds_change>>c.shares_remaining>>world.month_counter;c.owner_code=owner;c.commerce_type=type;c.stock_index=stock;
   }else if(op=='A'){
    decision.options.clear();int base,mode;in>>base>>mode;
    for(unsigned i=0;i<12;++i){DecisionOption o;o.value=i;o.subject=CardTarget{CardTargetKind::stock,static_cast<std::uint16_t>(i)};decision.options.push_back(o);}
    decision.options.push_back({"",-1});if(mode){decision.options.push_back({"",0});decision.options.push_back({"",0,{},CardTarget{CardTargetKind::actor,0}});decision.options.push_back({"",0,{},CardTarget{CardTargetKind::stock,99}});}
   }else if(op=='U')in>>accepted;
   else if(op=='Z'){int n;in>>n;pad.set_scale(n);}
   else if(op=='D'||op=='G'){
    bool showpad;int base,has;in>>f.ticks>>f.pointer_x>>f.pointer_y>>f.pointer_down>>showpad>>base>>has;
    for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;buttons.clear();
    if(op=='D')screen.draw(host,world,player,pad,actions);else screen.draw_card_target(host,world,player,has?&decision:nullptr,base,respond);
    if(showpad&&pad.active()){buttons.clear();pad.draw(host);}
   }else if(op=='X'){int id;in>>id;for(auto &b:buttons)if(b.id==id&&b.enabled){auto a=b.action;buttons.clear();a();break;}}
   else if(op=='K'){int n;in>>n;pad.key(host,char(n));}
   else if(op=='B')screen.cancel(host,actions);
   else if(op=='R')screen.reset();
   else if(op=='E')pad.cancel(host);
   else return 3;
   if(!old.empty()&&old!=world.export_save())throw std::runtime_error("stock UI changed World DAT");
   std::cout<<result;p(screen.selected?int(*screen.selected):-1);p(screen.page);p(screen.info_open);p(screen.popup_until_);s(screen.popup_);
   p(pad.active_);p(pad.dragging_);p(pad.x_);p(pad.y_);p(pad.scale_);p(pad.maximum_);s(pad.text_);p(bool(pad.done_));
   p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
   p(calls.size());for(auto &c:calls)for(auto v:c)p(v);std::cout<<'\n';
   if(op=='D'||op=='G'){std::vector<char> raw;raw.reserve(canvas.pixels.size()*2);for(auto v:canvas.pixels){raw.push_back(char(v));raw.push_back(char(v>>8));}std::cout.write(raw.data(),raw.size());}std::cout.flush();++step;
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
