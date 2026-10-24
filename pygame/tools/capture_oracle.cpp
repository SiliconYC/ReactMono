// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: actual native_audio capture limit and PCM16 writer, no device or MIDI.
#include "native_audio.cpp"
#include <bit>
#include <iostream>
int main(int argc,char **argv){
 if(argc!=2)return 2;
 rich4::audio::Audio a(".",false);auto &m=*a.impl_;m.capture_path=argv[1];
 m.capture.reserve(std::size_t(48000)*2*60);
 std::array<float,1024> block{};std::size_t n=0;
 for(;;){std::uint32_t bits=0;unsigned k=0;for(;k<4;++k){int b=std::cin.get();if(b<0)break;bits|=std::uint32_t(b)<<(k*8);}if(k!=4){if(k)return 3;break;}
  block[n++]=std::bit_cast<float>(bits);if(n==block.size()){m.capture_block_locked(block);n=0;}
 }
 if(n)m.capture_block_locked(std::span(block).first(n));
}
