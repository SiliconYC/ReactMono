// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only real-asset render adapter. Pixel files remain local temporary data.
#include "rich4/board_renderer.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

void u32(std::ostream &out,std::uint32_t n){for(unsigned i=0;i<4;++i)out.put(static_cast<char>((n>>(8*i))&255));}
int main(int argc,char **argv){
    if(argc!=4)return 2;
    try{
        rich4::board::Renderer renderer(argv[1],static_cast<std::uint8_t>(std::stoi(argv[2])));
        std::filesystem::create_directories(argv[3]);
        std::string op;unsigned step=0;
        while(std::cin>>op){
            if(op!="S"&&op!="G")return 3;
            int cx,cy,rotation,left,top,right,bottom,width,height,fill,mask;
            std::cin>>cx>>cy>>rotation>>left>>top>>right>>bottom>>width>>height>>fill>>mask;
            rich4::board::Camera camera{{cx,cy},static_cast<std::uint8_t>(rotation),{left,top,right,bottom}};
            std::size_t np,no,nl,nf,ns,nc,nw;std::cin>>np>>no>>nl>>nf>>ns>>nc>>nw;
            std::vector<rich4::board::PlayerSprite> players(np);
            std::vector<rich4::board::ObjectSprite> objects(no);
            std::vector<rich4::board::PropertyState> lands(nl),facilities(nf),commercials(nc);
            std::vector<rich4::board::SpecialPlayerSprite> actors(ns);
            std::vector<rich4::board::PropertyOwner> owners(nw);
            for(auto &p:players){int c,d,a,t,color,slot,active,walk,water,sleep,injury,toss,pose;
                std::cin>>p.position.x>>p.position.y>>c>>d>>a>>t>>color>>slot>>active>>walk>>water>>sleep>>injury>>toss>>pose;
                p.character=c;p.direction=d;p.animation_frame=a;p.traffic_method=t;p.color=color;p.slot=slot;
                p.active=active;p.walking=walk;p.on_water=water;p.sleepwalking=sleep;p.injured=injury;p.tossing=toss;p.special_pose=pose;}
            for(auto &p:objects){int k,d,a,f;std::cin>>p.position.x>>p.position.y>>k>>d>>a>>f;p.kind=k;p.direction=d;p.animation_frame=a;p.follow=f;}
            auto properties=[&](auto &items){for(auto &p:items){unsigned id,o,l,t,s;std::cin>>id>>o>>l>>t>>s;p.id=id;p.owner=o;p.level=l;p.type=t;p.temporary=s;}};
            properties(lands);properties(facilities);
            for(auto &p:actors){int s,d,a,active,walk,water,sleep;std::cin>>p.position.x>>p.position.y>>s>>d>>a>>active>>walk>>water>>sleep;
                p.slot=s;p.direction=d;p.animation_frame=a;p.active=active;p.walking=walk;p.on_water=water;p.sleepwalking=sleep;}
            properties(commercials);
            for(auto &p:owners){unsigned c,h;std::cin>>c>>h;p.color=c;p.character=h;}
            if(!std::cin)return 4;
            auto image=rich4::graphics::make_canvas(width,height,static_cast<std::uint16_t>(fill));
            if(mask){image.opaque_pixels.resize(image.pixels.size());for(std::size_t i=0;i<image.pixels.size();++i)image.opaque_pixels[i]=i%3==0;if(mask==2)image.opaque_pixels.pop_back();}
            rich4::board::Scene scene{players,objects,lands,facilities,actors,commercials,owners};
            rich4::board::RenderStats stats;
            unsigned status=0;
            try{stats=op=="G"?renderer.render_ground(image,camera):renderer.render(image,scene,camera);}
            catch(const std::exception &e){status=1;std::cerr<<"case "<<step<<": "<<e.what()<<'\n';}
            std::cout<<status<<' '<<stats.ground_tiles<<' '<<stats.road_markers<<' '<<stats.sprites<<'\n';
            std::ofstream out(std::filesystem::path(argv[3])/(std::to_string(step++)+".bin"),std::ios::binary);
            u32(out,image.pixels.size());u32(out,image.opaque_pixels.size());
            for(auto p:image.pixels){out.put(static_cast<char>(p&255));out.put(static_cast<char>(p>>8));}
            for(auto p:image.opaque_pixels)out.put(static_cast<char>(p));
            if(!out)throw std::runtime_error("snapshot write failed");
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
