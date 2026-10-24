// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: fixed original MonthlyScreens, real font/assets, explicit figures and recorded sound requests.
#include "screens/monthly.hpp"
#include <iostream>
#include <sstream>
namespace {
std::string hex(std::string_view s){if(s.empty())return "-";constexpr char h[]="0123456789abcdef";std::string r;for(unsigned char c:s){r+=h[c>>4];r+=h[c&15];}return r;}
template<class T>std::uint64_t digest(const T &values){std::uint64_t h=1469598103934665603ULL;for(auto v:values){h^=std::uint64_t(v);h*=1099511628211ULL;}return h;}
}
int main(int argc,char **argv){
    if(argc!=3)return 2;
    try{
        using namespace rich4;native::Artwork art(argv[1]);ui::Font font(argv[2]);World world;
        for(unsigned i=0;i<26;++i){auto bytes=art.archive(i<2?'p':'d').decode(i<2?16+i:414+i);flc::Decoder d(std::move(bytes));while(d.next()){}if(d.decoded_frames()!=d.frame_count())throw std::runtime_error("monthly movie incomplete");}
        auto canvas=graphics::make_canvas(640,480,0);std::vector<native::Button> buttons;native::Frame frame(canvas,art,font,buttons);
        std::unique_ptr<native::monthly::MonthlyScreens> screen;std::vector<std::pair<int,int>> calls;
        auto p=[](auto v){std::cout<<' '<<static_cast<long long>(v);};
        auto h=[](auto v){std::cout<<' '<<v;};
        auto figures=[&](const MonthlyFigures &f){p(f.active);for(auto v:f.characters)p(v);p(f.dividends.size());for(auto &r:f.dividends){p(r.stock);p(r.earnings);for(auto v:r.payout)p(v);}for(auto v:f.tickets)p(v);p(f.pool);p(f.number);p(f.winner);for(auto &a:{f.cash,f.deposit,f.interest,f.balance,f.total})for(auto v:a)p(v);p(f.loans);for(auto v:f.unlucky_days)p(v);for(auto v:f.income)p(v);for(auto v:f.spending)p(v);p(f.champion);p(f.unlucky);};
        auto movie=[&](const auto &m){p(bool(m.decoder));if(m.decoder){auto &d=*m.decoder;p(d.width());p(d.height());p(d.frame_count());p(d.delay_ms());p(d.decoded_frames());p(d.cursor_);h(digest(d.indices()));h(digest(d.palette()));}auto &g=m.still;p(g.width);p(g.height);p(g.origin_x);p(g.origin_y);h(digest(g.pixels));h(digest(g.opaque_pixels));p(m.x);p(m.y);p(m.plays);p(m.elapsed);p(m.running);p(m.overlay);};
        auto fixture=[&](unsigned ch,unsigned mask,unsigned v){MonthlyFigures f;f.active=mask;std::vector<unsigned> slots;for(unsigned i=0;i<4;++i){f.characters[i]=(ch+i*3)%12;if(mask&(1<<i))slots.push_back(i);f.cash[i]=52000+9000*int(i);f.deposit[i]=10000+15000*int(i);f.interest[i]=f.deposit[i]/10;f.balance[i]=f.deposit[i]+f.interest[i];f.total[i]=f.cash[i]+f.balance[i]+40000;f.income[i]=i==3?0xffffffffU:800+31*i;f.spending[i]=i==2?0x80000000U:1500*i;f.unlucky_days[i]=i*3;}
            f.loans=1<<slots.front();for(auto i:slots)if(f.loans&(1<<i)){f.interest[i]=0;f.balance[i]=f.deposit[i];}
            for(unsigned i=0;i<12;++i){DividendRow r{std::uint8_t(i),12000-2500*int(i),{}};r.payout={r.earnings/2,r.earnings/4,0,r.earnings/4};f.dividends.push_back(r);}
            for(unsigned n=0;n<36;n+=3)f.tickets[n]=slots[(n/3)%slots.size()]+1;
            f.pool=27000;f.number=v%2?29:7;f.winner=f.tickets[f.number-1]?f.tickets[f.number-1]-1:-1;
            f.champion=slots.back();f.unlucky=v%3==0?int(slots.front()):v%3==1?-1:f.champion;return f;};
        unsigned step=0;std::string line;
        while(std::getline(std::cin,line)){
            std::istringstream in(line);char op;in>>op;calls.clear();int result=-1;
            if(op=='N'){unsigned map;in>>map;NewGameOptions opt;opt.map_id=map%4;opt.stage_id=map/4;world=World::from_map_resource(art.archive('m').decode(map*2+1),opt);buttons.clear();screen=std::make_unique<native::monthly::MonthlyScreens>(native::monthly::Sound{[&](auto n){calls.emplace_back(0,n);},[&](auto n){calls.emplace_back(1,n);return unsigned(2000+n*37%1700);}});}
            else if(op=='E'){unsigned kind,has,ch,mask,v;in>>kind>>has>>ch>>mask>>v;EffectEvent e;e.kind=EffectKind(kind);if(has)e.monthly=fixture(ch,mask,v);screen->enqueue(e);}
            else if(op=='F'){unsigned dt;in>>dt;for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;buttons.clear();auto before=world.export_save();screen->draw(frame,world,dt);if(before!=world.export_save())throw std::runtime_error("monthly draw modified world");}
            else if(op=='X'){int id;in>>id;for(auto &b:buttons)if(b.id==id){auto action=b.action;buttons.clear();action();break;}}
            else if(op=='S'){bool skip;in>>skip;screen->set_skip(skip);}
            else if(op=='C')screen->clear();
            else if(op=='V'){unsigned k,has;in>>k>>has;EffectEvent e;e.kind=EffectKind(k);if(has)e.monthly=MonthlyFigures{};result=native::monthly::handles(e);}
            else return 3;
            std::cout<<result;p(screen->skip_);std::cout<<' '<<hex(screen->shot());p(screen->queue_.size());for(auto &e:screen->queue_){p(e.kind);figures(*e.monthly);}
            p(bool(screen->current_));if(screen->current_){auto &x=*screen->current_;p(x.event.kind);figures(*x.event.monthly);figures(x.figures);p(x.state);p(x.counter);p(x.tick_ms);p(x.elapsed);p(x.tapped);p(x.skip_wait);p(x.shown);auto &b=x.bubble;p(b.frame);p(b.x);p(b.y);p(b.dx);p(b.dy);std::cout<<' '<<hex(b.text);p(b.remaining_ms);p(b.up);movie(x.movie);movie(x.second);p(x.layout);p(x.lady_mode);p(x.spotlight);p(x.hidden);p(x.award);p(x.cards);p(x.lineup);p(x.happy);p(x.lined);p(x.balls);p(x.green);p(x.plate);p(x.eye_patch);p(x.mouth_patch);p(x.left_patch);p(x.blink);p(x.blink_step);p(x.mouth_hold);p(x.seed);p(x.closing);}
            p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}p(calls.size());for(auto [k,n]:calls){p(k);p(n);}std::cout<<'\n';
            if(op=='F')for(auto v:canvas.pixels){std::cout.put(char(v));std::cout.put(char(v>>8));}std::cout.flush();++step;
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
