// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only observer. Removal/finance hooks are explicitly partial, not a game backend.
#include "rich4/gods.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>

int main(int argc, char **argv) {
    try {
        if (argc == 2 && std::string(argv[1]) == "spinner") {
            unsigned kind, seed, stop, computer;
            while (std::cin >> kind >> seed >> stop >> computer) {
                rich4::Random rng(seed);
                rich4::gods::MoneySpinner spinner(kind);
                unsigned frozen = 0;
                for (unsigned frame = 0; frame < 2000; ++frame) {
                    if (frame == stop) spinner.stop();
                    spinner.tick(rng,computer);
                    std::cout << frame << ' ' << spinner.phase() << ' ' << spinner.amount() << ' ' << rng.state();
                    for (auto digit : spinner.digits()) std::cout << ' ' << unsigned(digit);
                    std::cout << '\n';
                    if (spinner.finished() && ++frozen == 5) break;
                    if (frame == 1999) throw std::runtime_error("spinner timeout");
                }
                std::cout << "end\n";
            }
            return 0;
        }
        if (argc != 4) return 2;
        std::ifstream file(argv[1], std::ios::binary);
        std::vector<std::uint8_t> bytes{std::istreambuf_iterator<char>(file), {}};
        auto w = rich4::World::from_save(rich4::SaveFile::decode(bytes));
        rich4::Random rng(static_cast<std::uint32_t>(std::stoul(argv[3])));
        std::filesystem::create_directories(argv[2]);
        unsigned step = 0;
        char op;
        int actor, object, node, kind, god, attached, traffic, absent, owner, level, base, lease, money, upgraded, mask, ending, mutate, modifier, automate;
        unsigned nodeflags, code;
        while (std::cin >> op >> actor >> object >> node >> kind >> god >> attached >> traffic >> absent >> nodeflags >> code >> owner >> level >> base >> lease >> money >> upgraded >> mask >> ending >> mutate >> modifier >> automate) {
            if (actor >= 0 && static_cast<std::size_t>(actor) < w.players.size()) {
                auto &p = w.players[actor]; p.state.node_id=node; p.state.traffic_method=traffic;
                p.status.god_info=god; p.status.days_in_hotel=absent; p.status.attached_bomb=0;
                p.status.god_luck_modifier=p.status.money_fortune_modifier=p.status.other_fortune_modifier=modifier;
            }
            if (object > 0 && static_cast<std::size_t>(object) <= w.objects.size()) {
                auto &o=w.objects[object-1]; o.kind=kind; o.attached_player=attached; o.node_id=node;
            }
            if (node >= 0 && static_cast<std::size_t>(node) < w.nodes.size()) {w.nodes[node].flags=nodeflags; w.nodes[node].type_and_index=code;}
            if (code>2000 && code<4000 && code-2000<w.lands.size()) {auto &p=w.lands[code-2000];p.economy.owner_code=owner;p.economy.level=level;p.land_price=base;}
            if (code>4000 && code<6000 && code-4000<w.facilities.size()) {auto &p=w.facilities[code-4000];p.owner_code=owner;p.level=level;p.land_price=base;}
            w.lease_mode=lease;
            std::vector<std::int64_t> calls;
            auto record=[&](int k,int a=0,int b=0,int c=0,int d=0){calls.insert(calls.end(),{k,a,b,c,d});};
            rich4::gods::Callbacks cb;
            if(mask&1) cb.remove_object=[&](auto id){record(1,id);if(mutate){for(auto &p:w.players)if(p.status.god_info==id)p.status.god_info=0;auto &o=w.objects.at(id-1);o.node_id=0;o.attached_player=0;}};
            if(mask&2) cb.choose_money=[&](auto k){auto amount=automate?rich4::gods::auto_money(k,rng):money;record(2,k,amount);return amount;};
            if(mask&4) cb.pay=[&](auto a,auto b,auto c,auto d){record(3,a,b,c,d);};
            unsigned overcalls=0;
            if(mask&8) cb.game_over=[&]{bool over=overcalls++>=static_cast<unsigned>(ending);record(4,over);return over;};
            if(mask&16) cb.hospital=[&](auto a,auto b){record(5,a,b);if(mutate)w.players.at(a).status.days_in_hospital=b;};
            if(mask&32) cb.voice=[&](auto a,auto b){record(6,a,b);};
            if(mask&64) cb.upgrade_property=[&](auto a){record(7,a,upgraded);return upgraded;};
            if(mask&128) cb.downgrade_property=[&](auto a){record(8,a);};
            if(mask&256) cb.hostility=[&](auto a,auto b,auto c){record(9,a,b,c);};
            if(mask&512) cb.appeared=[&](auto a,auto b){record(10,a,b);};
            if(mask&1024) cb.arrival=[&](auto a,auto b){record(11,a,b);};
            if(mask&2048) cb.leaving=[&](auto a,auto b){record(12,a,b);};
            if(mask&4096) cb.sound=[&](auto a,auto b){record(13,a,b);};
            if(mask&8192) cb.dog=[&](auto a,auto b){record(14,a,b);};
            int status=0,returned=0;
            rich4::gods::Result r;
            try {
                using namespace rich4::gods;
                if(op=='a')r=attach(w,rng,actor,object,node,cb);
                else if(op=='d')r=detach(w,actor,cb);
                else if(op=='t')r=touch(w,rng,actor,object,upgraded&1,cb);
                else if(op=='p')r=after_property(w,actor,node,cb);
                else if(op=='b')r=after_successful_purchase(w,rng,actor,node,cb);
                else if(op=='q')returned=attachable(w,object);
                else return 3;
            }catch(const std::out_of_range &){status=2;}
            catch(const std::invalid_argument &){status=1;}
            catch(const rich4::SaveError &){status=1;}
            std::cout<<status<<' '<<rng.state()<<' '<<r.supported<<' '<<r.applied<<' '<<r.stop_movement<<' '<<returned<<' '<<calls.size()/5;
            for(auto n:calls)std::cout<<' '<<n;
            std::cout<<'|'<<r.message<<'\n';
            auto snapshot=w.export_save();
            std::ofstream out(std::filesystem::path(argv[2])/(std::to_string(step++)+".dat"),std::ios::binary);
            out.write(reinterpret_cast<const char*>(snapshot.data()),snapshot.size());
            if(!out)throw std::runtime_error("snapshot write failed");
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
