// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: direct original Limiter, raw IEEE float32 input/output and full private state.
#include "audio_limiter.hpp"
#include <bit>
#include <cstdint>
#include <iostream>
#include <sstream>
#include <vector>
int main(){
 std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 rich4::audio::Limiter limiter(48000);std::string line;
 while(std::getline(std::cin,line)){
  std::istringstream in(line);char op;in>>op;std::vector<float> samples;std::size_t limited=0;
  if(op=='N'){std::uint32_t rate,ceiling,release;in>>rate>>ceiling>>release;limiter=rich4::audio::Limiter(std::bit_cast<float>(rate),std::bit_cast<float>(ceiling),std::bit_cast<float>(release));}
  else if(op=='B'){
   unsigned n;in>>n;if(n>65536)return 3;samples.resize(n);
   for(auto &s:samples){std::uint32_t v=0;for(unsigned k=0;k<4;++k){int b=std::cin.get();if(b<0)return 4;v|=std::uint32_t(b)<<(8*k);}s=std::bit_cast<float>(v);}limited=limiter.process(samples);
  }else return 2;
  std::cout<<limited<<' '<<std::bit_cast<std::uint32_t>(limiter.ceiling_)<<' '<<std::bit_cast<std::uint32_t>(limiter.release_)<<' '<<std::bit_cast<std::uint32_t>(limiter.envelope_)<<' '<<std::bit_cast<std::uint32_t>(limiter.gain())<<' '<<samples.size()<<'\n';
  for(auto s:samples){auto v=std::bit_cast<std::uint32_t>(s);for(unsigned k=0;k<4;++k)std::cout.put(char(v>>(8*k)));}std::cout.flush();
 }
}
