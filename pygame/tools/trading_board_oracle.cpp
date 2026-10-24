// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: original TradingBoard and NumberPad, actual trading callbacks and complete DAT output.
#include "screens/market.cpp"
#include <sstream>
int main(int argc,char **argv){
 if(argc!=3)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;using namespace native::screens;native::Artwork art(argv[1]);ui::Font font(argv[2]);World world;
  auto canvas=graphics::make_canvas(640,480,0);std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);
  TradingBoard board;NumberPad pad;std::size_t actor=0;std::array<int,3> modes{-1,-1,-1};
  std::vector<std::vector<long long>> calls;Host host{f,[&](auto n){calls.push_back({0,n});},{}};
  TradingActions actions{
   [&](const trading::Listing &l){bool ok=modes[0]>=0?bool(modes[0]):trading::post(world,actor,l).applied;calls.push_back({1,int(l.kind),l.item,l.price,l.quantity,ok});return ok;},
   [&](std::size_t i){bool ok=modes[1]>=0?bool(modes[1]):trading::cancel(world,actor,i);calls.push_back({2,(long long)i,ok});return ok;},
   [&](std::size_t s,std::size_t i){bool ok=modes[2]>=0?bool(modes[2]):trading::buy(world,actor,s,i).applied;calls.push_back({3,(long long)s,(long long)i,ok});return ok;},
   [&]{calls.push_back({4});}};
  auto p=[](auto n){std::cout<<' '<<static_cast<long long>(n);};auto str=[&](const std::string &s){std::uint64_t h=14695981039346656037ULL;for(unsigned char c:s){h^=c;h*=1099511628211ULL;}p(s.size());std::cout<<' '<<h;};
  unsigned step=0;std::string line;
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;calls.clear();int result=-1;std::vector<std::uint8_t> old;
   if(op=='D')old=world.export_save();
   if(op=='N'){
    unsigned map,ch;in>>map>>ch;NewGameOptions opt;opt.map_id=map%4;opt.stage_id=map/4;for(unsigned i=0;i<4;++i)opt.players[i].character=(ch+3*i)%12;
    world=World::from_map_resource(art.archive('m').decode(map*2+1),opt);board.reset();pad.close();buttons.clear();actor=0;modes={-1,-1,-1};
   }else if(op=='W'){
    unsigned variant,owner;in>>variant>>owner;world.header.price_index=1+variant%5;
    for(unsigned s=0;s<4;++s){auto &p=world.players[s];p.state.cash=variant==9?0:1000000;p.state.bank_balance=0;p.state.controller_flags=1;
     for(unsigned j=0;j<12;++j){p.stocks[j].amount=(j+3)*(s+1);world.stocks[j].float_bits[2]=std::bit_cast<std::uint32_t>(float(10.25+j*1.5));}
     for(unsigned j=0;j<13;++j)p.state.tool_amounts[j]=1+j%3;
     for(unsigned j=0;j<15;++j)p.state.cards[j]=1+j+(variant%2)*15;
    }
    for(unsigned j=1;j<world.lands.size();++j){auto &l=world.lands[j];l.economy.owner_code=owner?owner:1+j%4;l.economy.level=(j+variant)%6;l.economy.chain_store=(j%7==0);l.expired_date=j%3?0:0x07c70c1f;}
    for(unsigned j=1;j<world.facilities.size();++j){auto &l=world.facilities[j];l.owner_code=owner?owner:1+j%4;l.level=(j+variant)%6;l.expired_date=j%2?0:0x07c80102;}
   }else if(op=='Z'){
    unsigned s;in>>s;auto &p=world.players[s];for(auto &h:p.stocks)h.amount=0;p.state.tool_amounts={};p.state.cards={};
    for(auto &l:world.lands)if(l.economy.owner_code==s+1)l.economy.owner_code=0;
    for(auto &l:world.facilities)if(l.owner_code==s+1)l.owner_code=0;
   }else if(op=='A')in>>actor;
   else if(op=='E')in>>modes[0]>>modes[1]>>modes[2];
   else if(op=='O'){unsigned s,k,id,q;int price;in>>s>>k>>id>>price>>q;result=trading::post(world,s,{OfferKind(k),std::uint16_t(id),price,std::uint16_t(q)}).applied;if(!result)throw std::runtime_error("fixture post failed");}
   else if(op=='B'){std::size_t s,i;in>>s>>i;result=trading::cancel(world,s,i);}
   else if(op=='V'){int v;in>>v>>board.category_>>board.tab_>>board.scroll_;board.view_=TradingBoard::View(v);pad.close();}
   else if(op=='D'){
    bool overlay;in>>f.ticks>>f.pointer_x>>f.pointer_y>>f.pointer_down>>overlay;
    for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;buttons.clear();
    board.draw(host,world,actor,pad,actions);if(overlay)pad.draw(host);
   }else if(op=='X'||op=='I'){int id;in>>id;if(op=='I'){unsigned item;in>>item;auto items=trading::listable_items(world,actor);auto it=std::find_if(items.begin(),items.end(),[&](auto &i){return int(i.kind)==id&&i.id==item;});if(it==items.end())throw std::runtime_error("fixture item missing");id=460+int(it-items.begin());}bool found=false;for(auto &b:buttons)if(b.id==id&&b.enabled){found=true;auto a=b.action;buttons.clear();a();break;}if(!found)throw std::runtime_error("expected button missing: "+std::to_string(id));}
   else if(op=='K'){int key;in>>key;pad.key(host,char(key));}
   else if(op=='C')board.cancel(host,actions);
   else if(op=='R'){board.reset();pad.close();buttons.clear();}
   else return 3;
   const auto dat=world.export_save();if(!old.empty()&&old!=dat)throw std::runtime_error("drawing changed World DAT");
   std::cout<<result;p(board.view_);p(board.category_);p(board.tab_);p(board.scroll_);p(bool(board.detail_));
   if(board.detail_){auto &q=*board.detail_;p(q.seller);p(q.index);p(q.offer.kind);p(q.offer.item);p(q.offer.price);p(q.offer.quantity);}
   str(board.prompt_);str(board.notice_);p(board.notice_until_);p(board.now_);p(board.suggestion_);
   p(pad.active_);p(pad.dragging_);p(pad.x_);p(pad.y_);p(pad.scale());p(pad.maximum());p(pad.value());str(pad.digits());p(bool(pad.done_));
   p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
   p(calls.size());for(auto &call:calls){p(call.size());for(auto v:call)p(v);}p(dat.size());std::cout<<'\n';
   if(op=='D'){std::vector<char> raw;raw.reserve(canvas.pixels.size()*2);for(auto v:canvas.pixels){raw.push_back(char(v));raw.push_back(char(v>>8));}std::cout.write(raw.data(),raw.size());}
   std::cout.write(reinterpret_cast<const char*>(dat.data()),dat.size());std::cout.flush();++step;
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
