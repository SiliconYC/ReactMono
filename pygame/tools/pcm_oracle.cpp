// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: actual original public PCM controls and render_block_locked, offline (no device).
// The constructor is disabled; real archives are installed and enabled explicitly to prevent
// a hardware thread racing the deterministic blocks. No rule engine is used.
#define SDL_GetTicksNS rich4_pcm_oracle_clock
#include "native_audio.cpp"
#undef SDL_GetTicksNS
#include <bit>
#include <iostream>
#include <sstream>
#include <type_traits>
static std::uint64_t pcm_clock=0;
extern "C" Uint64 SDLCALL rich4_pcm_oracle_clock(){return pcm_clock;}
int main(int argc,char **argv){
 if(argc!=2)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;std::unique_ptr<audio::Audio> player;std::vector<std::pair<std::string,std::string>> trace;std::string line;
  auto p=[](auto n){if constexpr(std::is_unsigned_v<decltype(n)>&&sizeof(n)==8)std::cout<<' '<<n;else std::cout<<' '<<static_cast<long long>(n);};
  auto text=[&](std::string_view s){std::uint64_t h=14695981039346656037ULL;for(unsigned char c:s)h=(h^c)*1099511628211ULL;p(s.size());p(h);};
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;trace.clear();int result=-1;bool accepted=true;std::vector<float> output;
   try{
    if(op=='N'){
     bool enabled;in>>enabled;player=std::make_unique<audio::Audio>(argv[1],false);auto &m=*player->impl_;m.enabled=enabled;
     if(enabled){m.effects.emplace(audio::asset_path(argv[1],"effect.mkf"));m.voices.emplace(audio::asset_path(argv[1],"speaking.mkf"));}
     player->set_trace([&](std::string_view a,std::string_view b){trace.emplace_back(a,b);});pcm_clock=0;
    }else if(op=='S'){unsigned i;in>>i;player->play_sound(i);}
    else if(op=='V'){unsigned i;in>>i;result=player->play_speech(i);}
    else if(op=='Q'){unsigned i;in>>i;player->queue_speech(i);}
    else if(op=='R'){unsigned ch,cat;in>>ch>>cat;player->play_voice(std::uint8_t(ch),std::uint16_t(cat));}
    else if(op=='L'){unsigned c,i;in>>c>>i;player->play_loop(i,audio::Loop(c));}
    else if(op=='T'){unsigned c;in>>c;player->stop_loop(audio::Loop(c));}
    else if(op=='A')player->stop_all_loops();
    else if(op=='X')player->stop_voice();
    else if(op=='U'){in>>pcm_clock;player->update();}
    else if(op=='B'){
     unsigned count;in>>count;if(count>1000)return 3;output.resize(std::size_t(count)*1024);
     for(unsigned i=0;i<count;++i)player->impl_->render_block_locked(std::span(output).subspan(std::size_t(i)*1024,1024));
    }else if(op=='D'){
     bool voice;unsigned index,n;in>>voice>>index>>n;if(n>65536)return 4;auto &samples=player->impl_->samples;
     if(samples.contains({voice,index}))throw std::runtime_error("PCM fixture may only insert a new cache entry");std::vector<float> data(n);
     for(auto &v:data){std::uint32_t bits=0;for(unsigned k=0;k<4;++k){int b=std::cin.get();if(b<0)return 5;bits|=std::uint32_t(b)<<(k*8);}v=std::bit_cast<float>(bits);}samples.emplace(std::pair{voice,index},std::move(data));
    }else return 6;
   }catch(const std::exception &){accepted=false;}
   auto &m=*player->impl_;
   const auto source=[&](const std::vector<float> *ptr){for(const auto &[key,pcm]:m.samples)if(&pcm==ptr)return key;throw std::runtime_error("unowned PCM pointer");};
   std::cout<<accepted;p(result);p(m.enabled);p(player->voice_active());
   for(const auto &loop:m.loops){p(bool(loop));if(loop)p(*loop);}
   p(m.clips.size());for(const auto &c:m.clips){auto [voice,i]=source(c.samples);p(voice);p(i);p(c.samples->size());p(c.position);p(c.voice);p(c.loop);p(int(c.channel));}
   p(m.speech_queue.size());for(const auto &q:m.speech_queue){auto [voice,i]=source(q.samples);p(q.index);p(voice);p(i);}
   p(m.samples.size());for(auto &[key,pcm]:m.samples){p(key.first);p(key.second);p(pcm.size());}
   const auto &s=m.stats;p(s.rendered_frames);p(s.nonzero_samples);p(s.effects_started);p(s.voices_started);p(s.clips_completed);p(s.music_frames);p(s.underruns);p(s.starved_ms);p(s.clipped_samples);p(s.limited_samples);p(std::bit_cast<std::uint32_t>(s.peak));p(s.max_update_gap_ms);p(s.max_render_us);
   p(std::bit_cast<std::uint32_t>(m.limiter.ceiling_));p(std::bit_cast<std::uint32_t>(m.limiter.release_));p(std::bit_cast<std::uint32_t>(m.limiter.envelope_));p(std::bit_cast<std::uint32_t>(m.limiter.gain()));
   p(m.last_update_ns);p(m.error_reported);text(m.diagnostic);text(m.render_error);
   p(m.pending_log.size());for(auto &[a,b]:m.pending_log){text(a);text(b);}p(trace.size());for(auto &[a,b]:trace){text(a);text(b);}p(output.size());std::cout<<'\n';
   std::vector<char> bytes;bytes.reserve(output.size()*4);for(auto s:output){auto v=std::bit_cast<std::uint32_t>(s);for(unsigned k=0;k<4;++k)bytes.push_back(char(v>>(k*8)));}std::cout.write(bytes.data(),bytes.size());std::cout.flush();
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
