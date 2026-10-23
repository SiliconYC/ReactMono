// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only original native screen, no SDL/window/game backend. All source stays pinned.
#include "native_frame.hpp"
#include "screens/minigames.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
#include <sstream>

int main(int argc,char **argv) {
    if(argc!=4)return 2;
    try {
        using namespace rich4;
        native::Artwork art(argv[1]);
        ui::Font font(argv[2]);
        auto canvas=graphics::make_canvas(640,480,0);
        std::vector<native::Button> buttons;
        native::Frame frame(canvas,art,font,buttons);
        std::vector<std::pair<int,int>> cues;
        int current_loop=0;
        native::minigames::Sound sound;
        sound.play=[&](auto e){cues.emplace_back(0,e);};
        sound.loop=[&](auto e){cues.emplace_back(1,e);current_loop=e;};
        sound.stop_loop=[&]{cues.emplace_back(2,current_loop);current_loop=0;};
        native::minigames::MiniGames game(sound);
        std::optional<native::minigames::Result> result;
        std::filesystem::create_directories(argv[3]);
        std::string line;
        while(std::getline(std::cin,line)) {
            std::istringstream in(line);char op;in>>op;
            std::vector<long long> n{std::istream_iterator<long long>(in),{}};
            if(op=='n'){game.start(minigames::Game(n.at(0)),n.at(1),n.at(2),frame,n.at(3));result.reset();}
            else if(op=='t'){frame.ticks+=n.at(0);frame.pointer_x=n.at(1);frame.pointer_down=n.at(2);result=game.draw(frame);}
            else if(op=='p'){
                frame.pointer_x=n.at(0);frame.pointer_y=n.at(1);
                for(auto &b:buttons)if(b.enabled&&ui::contains(b.rectangle,frame.pointer_x,frame.pointer_y)){b.action();break;}
                result.reset();
            }else if(op=='s'){
                std::ofstream out(std::filesystem::path(argv[3])/(std::to_string(n.at(0))+".bin"),std::ios::binary);
                for(auto v:canvas.pixels){out.put(char(v&255));out.put(char(v>>8));}
                if(!out)throw std::runtime_error("pixel write failed");
                result.reset();
            }else return 3;
            std::cout<<bool(result);if(result)std::cout<<' '<<result->score<<' '<<result->draws;
            std::cout<<' '<<cues.size();for(auto [op,e]:cues)std::cout<<' '<<op<<' '<<e;
            std::cout<<'\n';cues.clear();
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
