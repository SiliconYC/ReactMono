// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only fixed-source probes. Public AI uses real projection; scan lists are explicit inputs.
#include "tools_ai.cpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <sstream>

int main(int argc,char **argv) {
    if(argc!=4)return 2;
    try {
        using namespace rich4;
        std::ifstream file(argv[1],std::ios::binary);
        std::vector<std::uint8_t> bytes{std::istreambuf_iterator<char>(file),{}};
        auto base=World::from_save(SaveFile::decode(bytes)),w=base;
        Random rng(static_cast<std::uint32_t>(std::stoul(argv[3])));
        std::filesystem::create_directories(argv[2]);
        unsigned step=0;
        std::string line;
        while(std::getline(std::cin,line)) {
            std::istringstream input(line);char op;input>>op;
            std::vector<std::int64_t> n{std::istream_iterator<std::int64_t>(input),{}};
            std::vector<std::int64_t> values,calls;
            using namespace tools_ai;
            Result r;
            int status=0;
            unsigned mask=op=='e'?n.at(2):op=='u'?n.at(1):0;
            unsigned scan=op=='e'?n.at(3):op=='u'?n.at(2):1;
            std::uint32_t carry=op=='e'?n.at(4):op=='u'?n.at(3):0;
            Callbacks cb;
            if(mask&1)cb.nearby_instances=[&](auto actor){
                calls.insert(calls.end(),{1,static_cast<std::int64_t>(actor),scan});
                std::vector<std::uint16_t> list;
                if(scan==3)return list;
                for(unsigned i=0;i<8;++i)list.push_back(0x8000|(1<<i));
                for(unsigned i=1;i<w.lands.size();++i)list.push_back(2000+i);
                for(unsigned i=1;i<w.facilities.size();++i)list.push_back(4000+i);
                if(scan==2)std::reverse(list.begin(),list.end());
                if(scan==4)list={0x8103,0x8000,2001,4001};
                if(scan==5)list={2001,4001};
                return list;
            };
            if(mask&2)cb.ownership_carry=[&]{calls.insert(calls.end(),{2,carry,0});return carry;};
            auto actor=[&](std::int64_t a){if(a<0||a>=4||std::size_t(a)>=w.players.size())throw std::invalid_argument("probe actor");return std::size_t(a);};
            try {
                if(op=='e')r=evaluate(w,rng,n.at(0),n.at(1),cb);
                else if(op=='u')r=choose(w,rng,n.at(0),cb);
                else if(op=='p'){auto path=preview(w,rng,actor(n.at(0)),n.at(1),n.at(2));values={path.crossed_junction,static_cast<std::int64_t>(path.nodes.size())};values.insert(values.end(),path.nodes.begin(),path.nodes.end());}
                else if(op=='v'){auto list=visible_roads(w,actor(n.at(0)));values.assign(list.begin(),list.end());}
                else if(op=='a'){if(n.at(3)>220)throw std::invalid_argument("probe radius");auto list=owned_area(w,actor(n.at(0)),{static_cast<int>(n.at(1)),static_cast<int>(n.at(2))},n.at(3));values.assign(list.begin(),list.end());}
                else if(op=='m'){if(n.at(2)>220)throw std::invalid_argument("probe radius");Selection sel(w,{static_cast<int>(n.at(0)),static_cast<int>(n.at(1))});for(unsigned i=3;i+2<n.size();i+=3)sel.insert({static_cast<int>(n[i]),static_cast<int>(n[i+1])},n[i+2]);auto list=sel.scan(n[2]);values.assign(list.begin(),list.end());}
                else if(op=='o')values.push_back(enemy(w,rng,actor(n.at(0))));
                else if(op=='t'){if(!is_land(w,n.at(0)))throw std::invalid_argument("probe land");values.push_back(toll(w,n.at(0)));}
                else if(op=='r')w=base;
                else if(op=='s')rng.seed(n.at(0));
                else if(op=='g'){w.camera_rotation=n.at(0);w.header.price_index=n.at(1);}
                else if(op=='c'){auto &p=w.players.at(n.at(0));p.state.controller_flags=n.at(1);p.status.card_strategy=n.at(2);p.status.rescue_strategy=n.at(3);p.state.traffic_method=n.at(4);p.state.cash=n.at(5);p.state.bank_balance=n.at(6);p.state.points=n.at(7);p.status.money_fortune_modifier=n.at(8);p.status.days_sleeping=n.at(9);p.status.god_info=n.at(10);p.state.node_id=n.at(11);p.state.last_node_id=n.at(12);p.state.x=n.at(13);p.state.y=n.at(14);}
                else if(op=='h')w.players.at(n.at(0)).status.hostility.at(n.at(1))=n.at(2);
                else if(op=='i')w.players.at(n.at(0)).state.tool_amounts.at(n.at(1))=n.at(2);
                else if(op=='d'){auto code=n.at(0);if(is_land(w,code)){auto &p=w.lands[code-2000];p.economy.owner_code=n.at(1);p.economy.level=n.at(2);p.economy.chain_store=n.at(3);p.land_price=n.at(4);p.price_per_level=n.at(5);}else if(is_facility(w,code)){auto &p=w.facilities[code-4000];p.owner_code=n.at(1);p.level=n.at(2);p.facility_type=n.at(3);p.land_price=n.at(4);p.toll_by_level[0]=n.at(5);}else throw std::invalid_argument("probe property");}
                else if(op=='n'){auto &p=w.nodes.at(n.at(0));p.flags=n.at(1);p.type_and_index=n.at(2);for(unsigned i=0;i<4;++i)p.neighbors[i]=n.at(3+i);p.x=n.at(7);p.y=n.at(8);}
                else if(op=='j'){auto &p=w.objects.at(n.at(0)-1);p.kind=n.at(1);p.node_id=n.at(2);p.attached_player=n.at(3);}
                else if(op=='z'){if(n.at(0)==0)w.prison_roster.at(n.at(1))=n.at(2);else w.hospital_roster.at(n.at(1))=n.at(2);}
                else if(op=='b'){auto &p=w.players.at(n.at(0)).status;p.days_in_hotel=n.at(1);p.days_disappearing=n.at(2);p.days_in_prison=n.at(3);p.days_in_hospital=n.at(4);}
                else return 3;
            }catch(const std::out_of_range &){status=2;}
            catch(const std::invalid_argument &){status=1;}
            catch(const SaveError &){status=1;}
            std::cout<<status<<' '<<rng.state()<<' '<<r.supported<<' '<<bool(r.decision);
            if(r.decision)std::cout<<' '<<r.decision->tool<<' '<<r.decision->target<<' '<<r.decision->destination;
            std::cout<<' '<<values.size();for(auto value:values)std::cout<<' '<<value;
            std::cout<<' '<<calls.size();for(auto value:calls)std::cout<<' '<<value;
            std::cout<<'|'<<r.message<<'\n';
            auto snapshot=w.export_save();
            std::ofstream out(std::filesystem::path(argv[2])/(std::to_string(step++)+".dat"),std::ios::binary);
            out.write(reinterpret_cast<const char*>(snapshot.data()),snapshot.size());
            if(!out)throw std::runtime_error("snapshot write failed");
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
