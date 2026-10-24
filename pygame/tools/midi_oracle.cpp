// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: original public music controls and complete offline PCM+MIDI render blocks.
#define SDL_GetTicksNS rich4_midi_oracle_clock
#include "native_audio.cpp"
#undef SDL_GetTicksNS
#include <bit>
#include <iostream>
#include <sstream>
static std::uint64_t midi_clock=0;
extern "C" Uint64 SDLCALL rich4_midi_oracle_clock(){return midi_clock;}
int main(int argc,char **argv){
 if(argc!=3)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;std::unique_ptr<audio::Audio> player;std::vector<std::pair<std::string,std::string>> trace;std::string line;
  auto p=[](auto n){std::cout<<' '<<static_cast<long long>(n);};
  auto text=[&](std::string_view s){std::uint64_t h=14695981039346656037ULL;for(unsigned char c:s)h=(h^c)*1099511628211ULL;p(s.size());std::cout<<' '<<h;};
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;trace.clear();bool accepted=true;std::vector<float> output;
   try{
    if(op=='N'){
     bool enabled,bank;in>>enabled>>bank;player=std::make_unique<audio::Audio>(argv[1],false);auto &m=*player->impl_;m.enabled=enabled;
     if(enabled){m.effects.emplace(audio::asset_path(argv[1],"effect.mkf"));m.voices.emplace(audio::asset_path(argv[1],"speaking.mkf"));m.initialize_music(bank?std::filesystem::path(argv[2]):std::filesystem::path(argv[1])/"__missing_midi_bank__.sf2");}
     player->set_trace([&](std::string_view a,std::string_view b){trace.emplace_back(a,b);});midi_clock=0;
    }else if(op=='P'){unsigned i;in>>i;player->push_music(audio::Music(i));}
    else if(op=='C'){unsigned i;in>>i;player->replace_music(audio::Music(i));}
    else if(op=='O')player->pop_music();
    else if(op=='M'){bool b;in>>b;player->set_music(b);}
    else if(op=='I'){unsigned i;in>>i;player->select_music(i);}
    else if(op=='S'){unsigned i;in>>i;player->play_sound(i);}
    else if(op=='V'){unsigned i;in>>i;player->play_speech(i);}
    else if(op=='Q'){unsigned i;in>>i;player->queue_speech(i);}
    else if(op=='L'){unsigned c,i;in>>c>>i;player->play_loop(i,audio::Loop(c));}
    else if(op=='T'){unsigned c;in>>c;player->stop_loop(audio::Loop(c));}
    else if(op=='U'){in>>midi_clock;player->update();}
    else if(op=='B'){
     unsigned count;in>>count;if(count>1000)return 3;output.resize(std::size_t(count)*1024);
     for(unsigned i=0;i<count;++i)player->impl_->render_block_locked(std::span(output).subspan(std::size_t(i)*1024,1024));
    }else return 4;
   }catch(const std::exception &){accepted=false;}
   auto &m=*player->impl_;std::cout<<accepted;p(m.enabled);p(player->music_available());p(player->music_enabled());p(player->music_track());p(m.context?int(*m.context):-1);p(player->music_depth());text(player->music_name());p(m.current_tick_locked());p(m.player?fluid_player_get_status(m.player.get()):-1);p(m.player_stale);p(m.resume_tick);p(bool(m.settings));
   p(m.music_stack.size());for(const auto &s:m.music_stack){p(s.context?int(*s.context):-1);p(s.track);p(s.tick);}
   p(m.midi_cache.size());for(const auto &[name,data]:m.midi_cache){text(name);text(std::string_view(reinterpret_cast<const char *>(data.data()),data.size()));}
   const auto &s=m.stats;p(s.rendered_frames);p(s.nonzero_samples);p(s.effects_started);p(s.voices_started);p(s.clips_completed);p(s.music_frames);p(s.underruns);p(s.starved_ms);p(s.clipped_samples);p(s.limited_samples);p(std::bit_cast<std::uint32_t>(s.peak));p(s.max_update_gap_ms);p(s.max_render_us);
   p(std::bit_cast<std::uint32_t>(m.limiter.envelope_));p(std::bit_cast<std::uint32_t>(m.limiter.gain()));text(m.diagnostic);text(m.render_error);
   p(m.pending_log.size());for(auto &[a,b]:m.pending_log){text(a);text(b);}p(trace.size());for(auto &[a,b]:trace){text(a);text(b);}p(output.size());std::cout<<'\n';
   for(float s:output){auto v=std::bit_cast<std::uint32_t>(s);for(unsigned k=0;k<4;++k)std::cout.put(char(v>>(k*8)));}std::cout.flush();
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
