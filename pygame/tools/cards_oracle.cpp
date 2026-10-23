// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only card observer/injector, not a session backend or viewport pick buffer.
#include "rich4/cards.hpp"
#include "rich4/inventory.hpp"
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>

struct Pending : std::runtime_error {using std::runtime_error::runtime_error;};
int main(int argc,char **argv) {
    if(argc!=4)return 2;
    try {
        using namespace rich4;
        std::ifstream file(argv[1],std::ios::binary);
        std::vector<std::uint8_t> bytes{std::istreambuf_iterator<char>(file),{}};
        auto base=World::from_save(SaveFile::decode(bytes)),w=base;
        Random rng(static_cast<std::uint32_t>(std::stoul(argv[3])));
        std::filesystem::create_directories(argv[2]);
        char op;
        int actor,card,tk,tv,ck,cv,pick,closed,free,frame,defense,auction,facility,scan,mutate;
        unsigned mask,price,step=0;
        while(std::cin>>op>>actor>>card>>tk>>tv>>ck>>cv>>mask>>pick>>closed>>free>>frame>>defense>>auction>>facility>>scan>>mutate>>price) {
            std::vector<std::int64_t> calls;
            auto record=[&](int k,std::vector<std::int64_t> values){calls.push_back(k);calls.push_back(values.size());calls.insert(calls.end(),values.begin(),values.end());};
            auto target=[](int k,int v){return CardTarget{static_cast<CardTargetKind>(k),static_cast<std::uint16_t>(v)};};
            auto pack=[](auto... values){return std::vector<std::int64_t>{static_cast<std::int64_t>(values)...};};
            CardCallbacks cb;
            if(mask&1)cb.voice=[&](auto a,auto b){record(1,pack(a,b));};
            if(mask&2)cb.pay=[&](auto a,auto b,auto c,auto d){record(2,pack(a,b,c,d));};
            if(mask&4)cb.add_prison=[&](auto a,auto b){record(3,pack(a,b));if(mutate){if(a<w.players.size())w.players[a].status.days_in_prison=b;else w.special_actors.at(a-4).inactive_state=1;}};
            if(mask&8)cb.try_mianzui_jiahuo=[&](auto a){record(4,pack(a,defense));if(defense==-2)throw Pending("choice");return defense;};
            if(mask&16)cb.update_stocks=[&](auto a){record(5,pack(a));if(mutate)w.stocks.at(a-1).float_bits[2]=price;};
            if(mask&32)cb.hostility=[&](auto a,auto b,auto c){record(6,pack(a,b,c));};
            if(mask&64)cb.turn_around=[&](auto a){record(7,pack(a));};
            if(mask&128)cb.change_building=[&](auto a,auto b){record(8,pack(a,b));};
            if(mask&256)cb.release_hotel=[&](auto a){record(9,pack(a));};
            if(mask&512)cb.auction_property=[&](auto a,auto b){record(10,pack(a,b,auction));if(auction==-2)throw Pending("choice");return bool(auction);};
            if(mask&1024)cb.choose_target=[&](auto a,std::span<const CardTarget> values)->std::optional<CardTarget>{
                std::vector<std::int64_t> args{a,static_cast<std::int64_t>(values.size())};
                for(auto t:values){args.push_back(static_cast<int>(t.kind));args.push_back(t.value);}record(11,args);
                if(pick==-2)throw Pending("choice");if(!pick)return {};
                if(pick==1)return values.front();if(pick==2)return values.back();return target(0,65535);
            };
            if(mask&2048)cb.choose_inventory=[&](auto a,auto b)->std::optional<CardTarget>{
                record(12,pack(a,b,pick));if(pick==-2)throw Pending("choice");if(!pick)return {};
                if(pick==1)return target(4,w.players.at(b).state.cards[0]);
                if(pick==2){for(unsigned i=0;i<13;++i)if(w.players.at(b).state.tool_amounts[i])return target(5,i+1);return {};}
                return target(5,65535);
            };
            if(mask&4096)cb.stolen=[&](auto a,auto b,CardTarget t,auto p){record(13,pack(a,b,static_cast<int>(t.kind),t.value,p));};
            if(mask&8192)cb.choose_facility_type=[&](auto a)->std::optional<std::uint8_t>{record(14,pack(a,facility));if(facility==-2)throw Pending("choice");if(facility==-1)return {};return static_cast<std::uint8_t>(facility);};
            if(mask&16384)cb.try_free=[&](auto a,auto b,auto c){record(15,pack(a,b,c,free));return bool(free);};
            if(mask&32768)cb.try_frame=[&](auto a,auto b){record(16,pack(a,b,frame));return frame;};
            if(mask&65536)cb.remove_object=[&](auto a){record(17,pack(a));if(mutate){auto &o=w.objects.at(a-1);o.node_id=0;o.attached_player=0;}};
            if(mask&131072)cb.detach_god=[&](auto a){record(18,pack(a));if(mutate)w.players.at(a).status.god_info=0;};
            if(mask&262144)cb.attach_god=[&](auto a,auto b){record(19,pack(a,b));if(mutate)w.players.at(a).status.god_info=b;};
            if(mask&524288)cb.market_closed=[&]{record(20,pack(closed));return bool(closed);};
            if(mask&1048576)cb.nearby_instances=[&](auto a){
                record(21,pack(a,scan));std::vector<std::uint16_t> values;
                if(scan==3)return values;
                for(unsigned i=0;i<8;++i)values.push_back(0x8000|(1<<i));
                for(unsigned i=1;i<w.lands.size();++i)values.push_back(2000+i);
                for(unsigned i=1;i<w.facilities.size();++i)values.push_back(4000+i);
                for(unsigned i=1;i<=w.objects.size();++i)values.push_back(0x8000|(i<<8));
                if(scan==2)std::reverse(values.begin(),values.end());
                if(scan==4)values={0x8001,0x8200,2002};
                if(scan==5)values={0xffff,0x8000,0};
                return values;
            };
            if(mask&2097152)cb.say=[&](auto a,auto b,auto c,auto d){record(22,pack(a,b,c,d));};
            if(mask&4194304)cb.passive_card=[&](auto a,auto b){record(23,pack(a,b));};
            int status=0,returned=0;
            CardResult r;
            std::vector<CardTarget> values;
            try {
                if(op=='u'){CardUse use;use.card_id=card;if(tk>=0)use.target=target(tk,tv);if(ck>=0)use.choice=target(ck,cv);r=apply_card(w,rng,actor,use,cb);}
                else if(op=='l')values=legal_card_targets(w,actor,card,cb);
                else if(op=='v')returned=active_card(card);
                else if(op=='r')w=base;
                else if(op=='h')w.players.at(actor).state.cards[0]=card;
                else return 3;
            }catch(const Pending &){status=3;}
            catch(const std::out_of_range &){status=2;}
            catch(const std::invalid_argument &){status=1;}
            catch(const SaveError &){status=1;}
            std::cout<<status<<' '<<rng.state()<<' '<<static_cast<int>(r.status)<<' '<<returned<<' '<<values.size();
            for(auto t:values)std::cout<<' '<<static_cast<int>(t.kind)<<' '<<t.value;
            std::cout<<' '<<calls.size();for(auto value:calls)std::cout<<' '<<value;
            std::cout<<'|'<<r.message<<'\n';
            auto snapshot=w.export_save();
            std::ofstream out(std::filesystem::path(argv[2])/(std::to_string(step++)+".dat"),std::ios::binary);
            out.write(reinterpret_cast<const char*>(snapshot.data()),snapshot.size());
            if(!out)throw std::runtime_error("snapshot write failed");
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
