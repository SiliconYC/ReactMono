// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: original bank and primary-stock screens; captures callbacks, never a game backend.
#include "screens/finance.hpp"
#include "screens/voices.hpp"
#include "rich4/calendar.hpp"
#include <iostream>
#include <sstream>
int main(int argc,char **argv){
 if(argc!=3)return 2;
 std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4; using namespace native::screens;
  native::Artwork art(argv[1]);ui::Font font(argv[2]);World world;
  auto canvas=graphics::make_canvas(640,480,0);std::vector<native::Button> buttons;
  native::Frame f(canvas,art,font,buttons);BankScreen bank;NumberPad pad;GameDecision decision;
  std::vector<std::pair<int,int>> calls;bool accepted=true;
  Host host{f,[&](auto n){calls.emplace_back(0,n);},{},false,[&](auto n){calls.emplace_back(1,n);}};
  BankActions actions{[&](int v,int n){calls.emplace_back(2+v,n);return accepted;}};
  auto p=[](auto n){std::cout<<' '<<static_cast<long long>(n);};
  auto s=[&](const std::string &str){std::uint64_t h=14695981039346656037ULL;for(unsigned char c:str){h^=c;h*=1099511628211ULL;}p(str.size());std::cout<<' '<<h;};
  unsigned step=0;std::string line;
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;calls.clear();int result=-1;
   std::vector<std::uint8_t> old; if(op=='D'||op=='G'||op=='K'||op=='X'||op=='B'||op=='P')old=world.export_save();
   if(op=='N'){
    unsigned map,ch,slot;in>>map>>ch>>slot;NewGameOptions opt;opt.map_id=map%4;opt.stage_id=map/4;
    for(unsigned i=0;i<4;++i)opt.players[i].character=(ch+i*3)%12;
    world=World::from_map_resource(art.archive('m').decode(map*2+1),opt);bank.reset();pad=NumberPad{};buttons.clear();
    decision={};decision.kind=DecisionKind::bank;decision.player=slot;accepted=true;
   }else if(op=='O'){
    unsigned mask;in>>mask;decision.options.clear();for(int i=0;i<7;++i)if(mask&(1<<i))decision.options.push_back({"",i});
   }else if(op=='W'){
    unsigned slot,days;int due;in>>slot;auto &v=world.players.at(slot);in>>v.state.cash>>v.state.bank_balance>>v.state.loan>>v.state.special_finance>>days>>due;
    v.status.days_bank_no_loans=days;v.status.loan_due_date=static_cast<std::uint32_t>(due);
   }else if(op=='M'){
    bool owner;in>>owner;auto slot=decision.player;world.players[slot].state.node_id=0;
    for(std::size_t i=0;i<world.nodes.size();++i){auto n=world.nodes[i].type_and_index;if(n>6000&&n<8000&&n-6000<world.commercials.size()){world.players[slot].state.node_id=i;world.commercials[n-6000].owner_code=owner?slot+1:0;break;}}
   }else if(op=='Z'){unsigned n;in>>n;world.commercials[0].stock_index=n;
   }else if(op=='T'){
    unsigned d,m,y;in>>d>>m>>y;world.header.date={static_cast<std::uint8_t>(d),static_cast<std::uint8_t>(m),static_cast<std::uint16_t>(y)};
   }else if(op=='S'){int n;in>>n;pad.set_scale(n);}
   else if(op=='U')in>>accepted;
   else if(op=='D'||op=='G'){
    bool showpad;in>>f.ticks>>f.pointer_x>>f.pointer_y>>f.pointer_down>>host.instant>>showpad;
    for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;
    buttons.clear();if(op=='D')bank.draw(host,world,decision,pad,actions);else draw_primary_stock(host,world,decision,pad,actions);
    if(showpad&&pad.active()){buttons.clear();pad.draw(host);}
   }else if(op=='J'){in>>decision.land_id>>decision.amount>>decision.max_amount;}
   else if(op=='K'){int n;in>>n;pad.key(host,char(n));}
   else if(op=='X'){int id;in>>id;for(auto &b:buttons)if(b.id==id&&b.enabled){auto a=b.action;buttons.clear();a();break;}}
   else if(op=='B')bank.cancel(host,decision,actions);
   else if(op=='P')pad.cancel(host);
   else if(op=='R')bank.reset();
   else if(op=='C')pad.close();
   else if(op=='I'){int n;in>>n;result=ids::atm_digit(n);}
   else if(op=='L'){int n,var;in>>n>>var;for(auto &l:native::voices::clerk_lines)if(l.voice==n){if(var--==0){s(std::string(l.text));std::cout<<' ';break;}}}
   else return 3;
   if(!old.empty()&&old!=world.export_save())throw std::runtime_error("bank changed World DAT");
   std::cout<<result;p(bank.stage_);p(bank.started_);p(bank.atm_dragging_);p(bank.side_panel_);p(bank.mode_);s(bank.atm_text_);
   p(bank.lines_.size());for(auto &v:bank.lines_)s(v);p(bank.line_started_);p(bank.side_started_);p(bank.popup_until_);s(bank.popup_);
   p(bank.said_);p(bank.voiced_said_);p(bank.voiced_index_);
   p(pad.active_);p(pad.dragging_);p(pad.x_);p(pad.y_);p(pad.scale_);p(pad.maximum_);s(pad.text_);p(bool(pad.done_));
   p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
   p(calls.size());for(auto [a,b]:calls){p(a);p(b);}std::cout<<'\n';
   if(op=='D'||op=='G'){std::vector<char> raw;raw.reserve(canvas.pixels.size()*2);for(auto v:canvas.pixels){raw.push_back(char(v));raw.push_back(char(v>>8));}std::cout.write(raw.data(),raw.size());}std::cout.flush();++step;
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
