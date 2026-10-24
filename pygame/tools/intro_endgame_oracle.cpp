// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: direct original IntroPlayer/EndgameScreen, genuine external frames and movies.
#include "screens/intro.cpp"
#include "screens/endgame.cpp"
#include <sstream>
#include <type_traits>
#include <zlib.h>
extern "C" std::uint64_t SDL_GetTicks(){return 0;}
template<class C> unsigned checksum(const C &values){std::vector<unsigned char> raw;raw.reserve(values.size()*sizeof(typename C::value_type));for(auto v:values)for(unsigned i=0;i<sizeof(v);++i)raw.push_back((std::uint64_t(v)>>(i*8))&255);return crc32(0,raw.data(),raw.size());}
int main(int argc,char **argv){
 if(argc!=3)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;using namespace native::screens;native::Artwork art(argv[1]);ui::Font font(argv[2]);
  for(int n=46;n<=70;++n){flc::Decoder d(art.archive('j').decode(n));while(d.next()){}if(!d.frame_count()||d.decoded_frames()!=d.frame_count())throw std::runtime_error("intro movie incomplete");}
  {flc::Decoder d(art.archive('d').decode(556));while(d.next()){}if(!d.frame_count()||d.decoded_frames()!=d.frame_count())throw std::runtime_error("bankruptcy movie incomplete");}
  auto intro=std::make_unique<native::IntroPlayer>(art);EndgameScreen end;
  auto canvas=graphics::make_canvas(640,480);std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);
  std::vector<std::pair<int,int>> calls;Host host{f,[&](auto n){calls.emplace_back(0,n);},{}};
  EndgameActions actions{[&]{calls.emplace_back(1,0);},[&](bool ok){calls.emplace_back(2,ok);},[&](unsigned m){calls.emplace_back(3,m);},[&]{calls.emplace_back(4,0);}};
  auto p=[](auto n){if constexpr(std::is_unsigned_v<decltype(n)>&&sizeof(n)==8)std::cout<<' '<<n;else std::cout<<' '<<static_cast<long long>(n);};
  auto image=[&](const graphics::Image &im){p(im.width);p(im.height);p(im.origin_x);p(im.origin_y);p(im.pixels.size());p(checksum(im.pixels));p(im.opaque_pixels.size());p(checksum(im.opaque_pixels));};
  auto movie=[&](const auto &m){p(bool(m));if(m){p(m->width());p(m->height());p(m->frame_count());p(m->delay_ms());p(m->decoded_frames());p(m->cursor_);p(checksum(m->indices()));p(checksum(m->palette()));}};
  std::string line;unsigned step=0;
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;calls.clear();
   if(op=='N'){intro=std::make_unique<native::IntroPlayer>(art);end=EndgameScreen{};buttons.clear();}
   else if(op=='S'){unsigned n,ch;in>>n;std::vector<std::uint8_t> chars;for(unsigned i=0;i<n;++i){in>>ch;chars.push_back(ch);}intro->start(chars);}
   else if(op=='K')intro->skip();
   else if(op=='O')end.open_play_again();
   else if(op=='G'){StageClear v;unsigned stage,map,ch,cleared,single,seed;in>>stage>>map>>ch>>cleared>>single>>seed;v.stage=stage;v.map=map;v.character=ch;v.cleared=cleared;v.single_human=single;v.seed=seed;end.open_stage_clear(v);}
   else if(op=='C')end.close();
   else if(op=='B'){unsigned n;in>>n;for(unsigned i=0;i<n;++i)end.stage_tick();}
   else if(op=='D'||op=='I'){
    for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;buttons.clear();
    if(op=='I'){unsigned elapsed;in>>elapsed;intro->draw(canvas,elapsed,[&](auto n){calls.emplace_back(0,n);});}
    else{bool hold;in>>f.ticks>>f.pointer_x>>f.pointer_y>>f.pointer_down>>hold>>host.instant;end.draw(host,hold,actions);}
   }else if(op=='X'){int id;in>>id;bool found=false;for(auto &b:buttons)if(b.id==id&&b.enabled){auto a=b.action;buttons.clear();a();found=true;break;}if(!found)throw std::runtime_error("expected ending button absent");}
   else return 3;
   std::cout<<-1;auto &i=*intro;p(i.active());p(i.shots_.size());p(i.index_);p(i.elapsed_);p(i.delay_);p(i.started_);p(i.sounded_);movie(i.movie_);image(i.frame_);
   for(auto &s:i.shots_){p(s.movie);p(s.x);p(s.y);p(s.start_sound);p(s.frame_sound);p(s.sound_frame);p(s.hold_ms);image(*s.still);}
   p(end.kind_);p(end.active());p(end.exit_button());p(end.last_ticks_);p(end.started_);p(end.step_);p(end.countdown_ms_);p(end.movie_ms_);movie(end.movie_);image(end.movie_frame_);
   p(end.info_.stage);p(end.info_.map);p(end.info_.character);p(end.info_.cleared);p(end.info_.single_human);p(end.info_.seed);std::ostringstream rng;rng<<end.random_;p(std::stoull(rng.str()));
   p(end.tick_ms_);p(end.scroll_);p(end.run_x_);p(end.run_y_);p(end.run_left_);p(end.winner_step_);p(end.god_step_);p(end.panel_y_);p(end.panel_speed_);p(end.picked_);p(end.picked_ticks_);p(end.leave_);
   p(bool(end.backdrop_));if(end.backdrop_)image(*end.backdrop_);p(bool(end.panel_));if(end.panel_)image(*end.panel_);for(auto &im:end.plates_)image(im);
   p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
   p(calls.size());for(auto [a,b]:calls){p(a);p(b);}std::cout<<'\n';
   if(op=='I'||op=='D'){for(auto v:canvas.pixels){std::cout.put(char(v));std::cout.put(char(v>>8));}}std::cout.flush();++step;
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
