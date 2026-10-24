// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: fixed original AuctionRoom/draw_lottery, real assets; callbacks observed, no runtime backend.
#include "screens/market.cpp"
#include <sstream>
int main(int argc,char **argv){
 if(argc!=3)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;using namespace native::screens;native::Artwork art(argv[1]);ui::Font font(argv[2]);World world;
  auto canvas=graphics::make_canvas(640,480,0);std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);
  AuctionRoom auction;LotteryFarewell farewell;GameDecision decision;std::uint32_t duration=0;
  std::vector<std::pair<int,int>> calls;Host host{f,[&](auto n){calls.emplace_back(0,n);},{}};
  auto respond=[&](auto n){calls.emplace_back(1,n);};auto goodbye=[&](bool picked){calls.emplace_back(2,picked);return duration;};
  auto &neon=neon_frames(art);flc::Decoder check(art.archive('p').decode(14));if(neon.size()!=check.frame_count()||neon.front().pixels.empty())throw std::runtime_error("neon preflight incomplete");
  auto p=[](auto n){std::cout<<' '<<static_cast<long long>(n);};auto str=[&](const std::string &s){std::uint64_t h=14695981039346656037ULL;for(unsigned char c:s){h^=c;h*=1099511628211ULL;}p(s.size());std::cout<<' '<<h;};
  unsigned step=0;std::string line;
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;calls.clear();std::vector<std::uint8_t> old;
   if(op=='D'||op=='F'||op=='L'||op=='X')old=world.export_save();
   if(op=='N'){
    unsigned map,ch;in>>map>>ch;NewGameOptions opt;opt.map_id=map%4;opt.stage_id=map/4;for(unsigned i=0;i<4;++i)opt.players[i].character=(ch+3*i)%12;
    world=World::from_map_resource(art.archive('m').decode(map*2+1),opt);auction.reset();farewell={};buttons.clear();decision={};
   }else if(op=='B'){
    unsigned kind,mask,count;in>>kind>>decision.player>>decision.land_id>>decision.amount>>mask>>count;decision.kind=DecisionKind(kind);decision.inactive_players=mask;decision.options.clear();
    for(unsigned i=0;i<count;++i){int value;in>>value;decision.options.push_back({"",value});}
   }else if(op=='W'){
    unsigned level,owner,mask;in>>world.public_fund>>level>>owner>>mask;
    if(world.lands.size()>1){world.lands[1].economy.level=level;world.lands[1].economy.owner_code=owner;}
    if(world.facilities.size()>1)world.facilities[1].owner_code=owner;
    for(unsigned i=0;i<36;++i)world.lottery_tickets[i]=mask?(i%5):0;
   }else if(op=='S'){std::size_t winner;std::int32_t price;std::uint16_t property;in>>winner>>price>>property;auction.start_sold(winner,price,property);}
   else if(op=='R')auction.reset();
   else if(op=='D'||op=='F'||op=='L'){
    bool has,voice;in>>f.ticks>>f.pointer_x>>f.pointer_y>>f.pointer_down>>host.instant>>has>>voice>>duration;
    for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;buttons.clear();
    if(op=='D')auction.draw(host,world,decision,respond);else if(op=='F')auction.draw_sold(host,world);else draw_lottery(host,world,decision,respond,has?&farewell:nullptr,voice?std::function<std::uint32_t(bool)>(goodbye):std::function<std::uint32_t(bool)>{});
   }else if(op=='X'){int id;in>>id;for(auto &b:buttons)if(b.id==id&&b.enabled){auto a=b.action;buttons.clear();a();break;}}
   else return 3;
   if(!old.empty()&&old!=world.export_save())throw std::runtime_error("auction/lottery UI changed World DAT");
   std::cout<<-1;p(bool(auction.bid_));if(auction.bid_){auto &b=*auction.bid_;str(b.key);p(b.index);p(b.action);p(b.price);p(b.started);}
   p(bool(auction.sold_));if(auction.sold_){auto &s=*auction.sold_;p(s.winner);p(s.price);p(s.property);p(s.started);p(s.sounded);}
   p(bool(farewell.option));if(farewell.option)p(*farewell.option);p(farewell.number);p(farewell.started);p(farewell.voice_ms);p(neon.size());
   p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
   p(calls.size());for(auto [a,b]:calls){p(a);p(b);}std::cout<<'\n';
   if(op=='D'||op=='F'||op=='L'){std::vector<char> raw;raw.reserve(canvas.pixels.size()*2);for(auto v:canvas.pixels){raw.push_back(char(v));raw.push_back(char(v>>8));}std::cout.write(raw.data(),raw.size());}std::cout.flush();++step;
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
