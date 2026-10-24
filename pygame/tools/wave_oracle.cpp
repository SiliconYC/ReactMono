// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: actual fixed native_audio.cpp::decode_wave; no Audio device is constructed.
#include "native_audio.cpp"
#include <bit>
#include <iostream>
#include <sstream>
int main(int argc,char **argv){
 if(argc!=2)return 2;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  using namespace rich4;std::map<char,std::unique_ptr<assets::Archive>> archives;std::string line;
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;std::vector<std::uint8_t> raw;std::vector<float> samples;bool ok=true;
   if(op=='W'){
    char lib;unsigned n;int cut;in>>lib>>n>>cut;if(lib!='e'&&lib!='s')return 3;
    if(!archives.contains(lib))archives.emplace(lib,std::make_unique<assets::Archive>(audio::asset_path(argv[1],lib=='e'?"effect.mkf":"speaking.mkf")));
    raw=archives.at(lib)->decode(n);if(cut>=0)raw.resize(std::min(raw.size(),std::size_t(cut)));
   }else if(op=='D'){
    unsigned size;in>>size;if(size>16000000)return 4;raw.resize(size);if(!std::cin.read(reinterpret_cast<char*>(raw.data()),raw.size()))return 5;
   }else return 6;
   try{samples=audio::decode_wave(raw);}catch(const std::exception &){ok=false;}
   std::cout<<ok<<' '<<samples.size()<<'\n';
   std::vector<char> bytes;bytes.reserve(samples.size()*4);for(float s:samples){auto v=std::bit_cast<std::uint32_t>(s);for(unsigned k=0;k<4;++k)bytes.push_back(char(v>>(8*k)));}std::cout.write(bytes.data(),bytes.size());std::cout.flush();
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
