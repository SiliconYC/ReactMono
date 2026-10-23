// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only tool observer; restoration changes are injected, not a full session rewind.
#include "rich4/tools.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>

int main(int argc,char **argv) {
    if(argc!=4)return 2;
    try {
        std::ifstream file(argv[1],std::ios::binary);
        std::vector<std::uint8_t> bytes{std::istreambuf_iterator<char>(file),{}};
        auto base=rich4::World::from_save(rich4::SaveFile::decode(bytes)),w=base;
        rich4::Random rng(static_cast<std::uint32_t>(std::stoul(argv[3])));
        std::filesystem::create_directories(argv[2]);
        char op;
        int actor,tool,target,destination,mask,restore,changed,mutate;
        unsigned step=0;
        while(std::cin>>op>>actor>>tool>>target>>destination>>mask>>restore>>changed>>mutate) {
            std::vector<std::int64_t> calls;
            auto record=[&](int k,int a=0,int b=0,int c=0){calls.insert(calls.end(),{k,a,b,c});};
            rich4::tools::Callbacks cb;
            if(mask&1)cb.robot=[&](auto a){record(1,a);if(mutate)++w.players.at(a).state.points;};
            if(mask&2)cb.remote_dice=[&](auto a,auto b){record(2,a,b);if(mutate)w.header.current_player=changed;};
            if(mask&4)cb.restore_last_state=[&]{record(3,restore,changed);if(restore)w.header.current_player=changed;return bool(restore);};
            if(mask&8)cb.upgrade=[&](auto a){record(4,a);};
            if(mask&16)cb.blast=[&](auto a,auto b,auto c){record(5,a,b,c);};
            if(mask&32)cb.before_teleport=[&](auto a){record(6,a);if(mutate)w.header.current_player=changed;};
            if(mask&64)cb.say=[&](auto a,auto b){record(7,a,b);};
            rich4::tools::Result r;
            unsigned returned=0;
            int status=0;
            try {
                if(op=='u')r=rich4::tools::use(w,rng,actor,tool,target,destination,cb);
                else if(op=='s')returned=rich4::tools::selection_flags(tool,target);
                else if(op=='d')returned=rich4::tools::dismount(w,actor);
                else if(op=='r')w=base;
                else return 3;
            }catch(const std::out_of_range &){status=2;}
            catch(const std::invalid_argument &){status=1;}
            catch(const rich4::SaveError &){status=1;}
            std::cout<<status<<' '<<rng.state()<<' '<<r.supported<<' '<<r.applied<<' '<<returned<<' '<<calls.size()/4;
            for(auto value:calls)std::cout<<' '<<value;
            std::cout<<'|'<<r.message<<'\n';
            auto snapshot=w.export_save();
            std::ofstream out(std::filesystem::path(argv[2])/(std::to_string(step++)+".dat"),std::ios::binary);
            out.write(reinterpret_cast<const char*>(snapshot.data()),snapshot.size());
            if(!out)throw std::runtime_error("snapshot write failed");
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
