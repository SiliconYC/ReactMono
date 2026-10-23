// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only original predicates and memory. Explicit callbacks are test inputs.
#include "cards_ai.cpp"
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
        auto base_world=World::from_save(SaveFile::decode(bytes)),w=base_world;
        Random rng(static_cast<std::uint32_t>(std::stoul(argv[3])));
        CardAiMemory memory;
        std::filesystem::create_directories(argv[2]);
        unsigned step=0;
        std::string line;
        while(std::getline(std::cin,line)) {
            std::istringstream input(line);char op;input>>op;
            std::vector<std::int64_t> n{std::istream_iterator<std::int64_t>(input),{}};
            std::vector<std::int64_t> values,calls;
            std::optional<CardUse> use;
            int status=0;
            auto scan=[&](unsigned mode) {
                std::vector<std::uint16_t> list;
                for(unsigned i=0;i<8;++i)list.push_back(0x8000|(1<<i));
                for(unsigned i=1;i<w.objects.size()+1;++i)list.push_back(0x8000|(i<<8));
                for(unsigned i=1;i<w.lands.size();++i)list.push_back(2000+i);
                for(unsigned i=1;i<w.facilities.size();++i)list.push_back(4000+i);
                if(mode==2)std::reverse(list.begin(),list.end());
                if(mode==3)list={};
                if(mode==4)list={0x8106,0x8002,0x8106,2001,2001,2002,2003,4001};
                if(mode==5)list={0x8100};
                if(mode==6){list.assign(260,2001);list.push_back(2002);}
                return list;
            };
            unsigned mask=(op=='p'?n.at(2):op=='u'?n.at(1):0);
            unsigned mode=(op=='p'?n.at(3):op=='u'?n.at(2):1);
            unsigned route=(op=='p'?n.at(4):op=='u'?n.at(3):0);
            bool closed=(op=='p'?n.at(5):op=='u'?n.at(4):0);
            CardCallbacks cb;
            if(mask&1)cb.nearby_instances=[&](auto actor){calls.insert(calls.end(),{1,static_cast<std::int64_t>(actor),mode});return scan(mode);};
            if(mask&2)cb.lookahead_nodes=[&](auto actor,auto count){
                calls.insert(calls.end(),{2,static_cast<std::int64_t>(actor),static_cast<std::int64_t>(count)});
                CardLookahead out;
                if(route==0){auto p=tools_ai::preview(w,rng,actor,count);out.nodes=p.nodes;out.crossed_junction=p.crossed_junction;}
                else if(route!=4){for(unsigned i=0;i<count;++i)out.nodes.push_back(route==5?65535:1+(route==2?count-i-1:i));out.crossed_junction=route==3;}
                return out;
            };
            if(mask&4)cb.market_closed=[&]{calls.insert(calls.end(),{3,closed,0});return closed;};
            auto actor=[&](std::int64_t a){if(a<0||a>=4||std::size_t(a)>=w.players.size())throw std::invalid_argument("probe actor");return std::size_t(a);};
            try {
                if(op=='u')use=choose_ai_card(w,rng,n.at(0),cb,n.at(5)?&memory:nullptr);
                else if(op=='p')values.push_back(predicate(w,rng,actor(n.at(0)),n.at(1),cb,memory,n.at(6)));
                else if(op=='m')memory={static_cast<std::uint32_t>(n.at(0)),static_cast<std::uint32_t>(n.at(1)),static_cast<std::uint32_t>(n.at(2))};
                else if(op=='x'){auto target=decode_target(n.at(0));values.push_back(bool(target));if(target){values.push_back(int(target->kind));values.push_back(target->value);}}
                else if(op=='v')values.push_back(monster_target(w,actor(n.at(0)),scan(n.at(1))));
                else if(op=='y'){auto god=nearest_god(w,actor(n.at(0)),scan(n.at(1)));values={bool(god),god?*god:0};}
                else if(op=='o')values.push_back(enemy(w,actor(n.at(0))));
                else if(op=='t'){if(!land(w,n.at(0))&&!facility(w,n.at(0)))throw std::invalid_argument("probe property");values.push_back(acquisition_cost(w,n.at(0)));}
                else if(op=='l')values.push_back(holding_cost(w.players.at(n.at(0)).stocks.at(n.at(1))));
                else if(op=='k'){auto &p=w.players.at(n.at(0));for(unsigned i=0;i<15;++i)p.state.cards[i]=n.at(1+i);}
                else if(op=='E')w.lands.at(n.at(0)).economy.street_name="AI-"+std::to_string(n.at(1));
                else if(op=='f'){auto &p=w.players.at(n.at(0)).status;p.days_tortoise_walking=n.at(1);p.attached_bomb=n.at(2);p.allied_player=n.at(3);}
                else if(op=='q'){auto &p=w.players.at(n.at(0)).stocks.at(n.at(1));p.amount=n.at(2);p.raw_cost_basis=n.at(3);}
                else if(op=='w'){auto &s=w.stocks.at(n.at(0));s.flags_4=n.at(1);s.suspension_days=n.at(2);s.float_bits[1]=n.at(3);s.float_bits[2]=n.at(4);}
                else if(op=='r')w=base_world;
                else if(op=='s')rng.seed(n.at(0));
                else if(op=='g'){w.camera_rotation=n.at(0);w.header.price_index=n.at(1);}
                else if(op=='c'){auto &p=w.players.at(n.at(0));p.state.controller_flags=n.at(1);p.status.card_strategy=n.at(2);p.status.rescue_strategy=n.at(3);p.state.traffic_method=n.at(4);p.state.cash=n.at(5);p.state.bank_balance=n.at(6);p.state.points=n.at(7);p.status.money_fortune_modifier=n.at(8);p.status.days_sleeping=n.at(9);p.status.god_info=n.at(10);p.state.node_id=n.at(11);p.state.last_node_id=n.at(12);p.state.x=n.at(13);p.state.y=n.at(14);}
                else if(op=='h')w.players.at(n.at(0)).status.hostility.at(n.at(1))=n.at(2);
                else if(op=='i')w.players.at(n.at(0)).state.tool_amounts.at(n.at(1))=n.at(2);
                else if(op=='d'){auto code=n.at(0);if(land(w,code)){auto &p=w.lands[code-2000];p.economy.owner_code=n.at(1);p.economy.level=n.at(2);p.economy.chain_store=n.at(3);p.land_price=n.at(4);p.price_per_level=n.at(5);}else if(facility(w,code)){auto &p=w.facilities[code-4000];p.owner_code=n.at(1);p.level=n.at(2);p.facility_type=n.at(3);p.land_price=n.at(4);p.toll_by_level[0]=n.at(5);}else throw std::invalid_argument("probe property");}
                else if(op=='n'){auto &p=w.nodes.at(n.at(0));p.flags=n.at(1);p.type_and_index=n.at(2);for(unsigned i=0;i<4;++i)p.neighbors[i]=n.at(3+i);p.x=n.at(7);p.y=n.at(8);}
                else if(op=='j'){auto &p=w.objects.at(n.at(0)-1);p.kind=n.at(1);p.node_id=n.at(2);p.attached_player=n.at(3);}
                else if(op=='z'){if(n.at(0)==0)w.prison_roster.at(n.at(1))=n.at(2);else w.hospital_roster.at(n.at(1))=n.at(2);}
                else if(op=='b'){auto &p=w.players.at(n.at(0)).status;p.days_in_hotel=n.at(1);p.days_disappearing=n.at(2);p.days_in_prison=n.at(3);p.days_in_hospital=n.at(4);}
                else return 3;
            }catch(const std::out_of_range &){status=2;}
            catch(const std::invalid_argument &){status=1;}
            catch(const SaveError &){status=1;}
            std::cout<<status<<' '<<rng.state()<<' '<<memory.parameter0<<' '<<memory.parameter1<<' '<<memory.parameter2<<' '<<bool(use);
            if(use){std::cout<<' '<<unsigned(use->card_id);auto target=[&](const auto &t){std::cout<<' '<<bool(t);if(t)std::cout<<' '<<int(t->kind)<<' '<<t->value;};target(use->target);target(use->choice);}
            std::cout<<' '<<values.size();for(auto value:values)std::cout<<' '<<value;
            std::cout<<' '<<calls.size();for(auto value:calls)std::cout<<' '<<value;
            std::cout<<'\n';
            auto snapshot=w.export_save();
            std::ofstream out(std::filesystem::path(argv[2])/(std::to_string(step++)+".dat"),std::ios::binary);
            out.write(reinterpret_cast<const char*>(snapshot.data()),snapshot.size());
            if(!out)throw std::runtime_error("snapshot write failed");
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
