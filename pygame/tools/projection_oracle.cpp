// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only projection/pose selector, no commercial resource is required.
#include "rich4/board_renderer.hpp"
#include <iostream>
#include <string>

int main(){
    std::string op;
    while(std::cin>>op){
        try {
            if(op=="P"||op=="U"){
                int r,x,y,l,t,bottom,right,px,py;
                std::cin>>r>>x>>y>>l>>t>>right>>bottom>>px>>py;
                if(!std::cin)return 2;
                rich4::board::Camera camera{{x,y},static_cast<std::uint8_t>(r),{l,t,right,bottom}};
                const auto point=op=="P"?rich4::board::project({px,py},camera):rich4::board::unproject({px,py},camera);
                std::cout<<"0 "<<bool(point);
                if(point)std::cout<<' '<<point->x<<' '<<point->y;
                std::cout<<'\n';
            }else if(op=="R"){
                int c,t,w,a,s,i,d,p;std::cin>>c>>t>>w>>a>>s>>i>>d>>p;
                if(!std::cin)return 2;
                rich4::board::PlayerSprite player;
                player.character=static_cast<std::uint8_t>(c);player.traffic_method=static_cast<std::uint8_t>(t);
                player.walking=w;player.on_water=a;player.sleepwalking=s;player.injured=i;player.tossing=d;player.special_pose=static_cast<std::uint8_t>(p);
                auto index=rich4::board::player_resource(player);std::cout<<"0 "<<index<<'\n';
            }else return 3;
        }catch(const std::invalid_argument&){std::cout<<"1\n";}
    }
}
