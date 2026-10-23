// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only observer/injector. Hooks do not stand in for real financing or map pick-buffer damage.
#include "rich4/events.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>

struct ChoicePending : std::runtime_error {using std::runtime_error::runtime_error;};
int main(int argc,char **argv) {
    if(argc!=4)return 2;
    try {
        std::ifstream file(argv[1],std::ios::binary);
        std::vector<std::uint8_t> bytes{std::istreambuf_iterator<char>(file),{}};
        auto base=rich4::World::from_save(rich4::SaveFile::decode(bytes)),w=base;
        rich4::Random rng(static_cast<std::uint32_t>(std::stoul(argv[3])));
        std::filesystem::create_directories(argv[2]);
        unsigned step=0;
        char op;
        int actor,id,mask,choice,target,mutate;
        while(std::cin>>op>>actor>>id>>mask>>choice>>target>>mutate) {
            std::vector<std::int64_t> calls;
            auto record=[&](int k,int a=0,int b=0,int c=0,int d=0){calls.insert(calls.end(),{k,a,b,c,d});};
            rich4::EventCallbacks cb;
            if(mask&1)cb.voice=[&](auto a,auto b){record(1,a,b);};
            if(mask&2)cb.pay=[&](auto a,auto b,auto c,auto d){record(2,a,b,c,d);if(mutate&&a>=0&&std::size_t(a)<w.players.size()&&(c&1))w.players[a].state.controller_flags=0;};
            if(mask&4)cb.add_prison=[&](auto a,auto b){record(3,a,b);if(mutate)w.players.at(a).status.days_in_prison=b;};
            if(mask&8)cb.add_hospital=[&](auto a,auto b){record(4,a,b);if(mutate)w.players.at(a).status.days_in_hospital=b;};
            if(mask&16)cb.disappear=[&](auto a,auto b,auto c){record(5,a,b,c);if(mutate)w.players.at(a).status.days_disappearing=b;};
            if(mask&32)cb.try_mianzui_jiahuo=[&](auto a){record(6,a,target);if(target==-2)throw ChoicePending("choice");return target;};
            if(mask&64)cb.set_loan_due_date=[&](auto a){record(7,a);if(mutate)w.players.at(a).status.loan_due_date=0x7ea021f;};
            if(mask&128)cb.sell_stock=[&](auto a,auto b,auto c,auto d){record(8,a,b,c,d);};
            if(mask&256)cb.auction=[&](auto a){record(9,a);if(choice==-2)throw ChoicePending("choice");};
            if(mask&512)cb.choose_card=[&](auto a,auto b){record(10,a,b,choice);if(choice==-2)throw ChoicePending("choice");return static_cast<std::uint8_t>(choice==1?w.players.at(b).state.cards[0]:choice==2?31:0);};
            if(mask&1024)cb.area_damage=[&](auto a,auto b,auto c,auto d){record(11,a,b,c,d);};
            if(mask&2048)cb.update_stocks=[&](auto a){record(12,a);};
            if(mask&4096)cb.news_picture=[&](auto a,auto b){record(13,a,b);};
            int status=0,returned=-1;
            rich4::EventResult r;
            rich4::EventSelection s;
            try {
                if(op=='n')r=rich4::apply_news_id(w,rng,id,cb);
                else if(op=='f')r=rich4::apply_fortune_id(w,rng,actor,id,cb);
                else if(op=='N')r=rich4::apply_news(w,rng,cb);
                else if(op=='F')r=rich4::apply_fortune(w,rng,actor,cb);
                else if(op=='e')returned=rich4::news_eligible(w,id);
                else if(op=='g'){auto value=rich4::fortune_eligible(w,actor,id);returned=value?int(*value):-1;}
                else if(op=='s')s=rich4::select_news(w);
                else if(op=='t')s=rich4::select_fortune(w,actor);
                else if(op=='r')w=base;
                else if(op=='u'){if(actor==0)w.news_cursor=id;else w.fortune_cursor=id;}
                else if(op=='d'){if(actor==0)w.news_deck.fill(id);else w.fortune_deck.fill(id);}
                else return 3;
            }catch(const ChoicePending &){status=3;}
            catch(const std::out_of_range &){status=2;}
            catch(const std::invalid_argument &){status=1;}
            catch(const rich4::SaveError &){status=1;}
            std::cout<<status<<' '<<rng.state()<<' '<<r.supported<<' '<<unsigned(r.event_id)<<' '<<r.property<<' '<<r.subject<<' '<<r.company<<' '<<r.value<<' '<<unsigned(r.players);
            for(auto amount:r.player_amounts)std::cout<<' '<<amount;
            std::cout<<' '<<returned<<' '<<unsigned(s.source_id)<<' '<<unsigned(s.event_id)<<' '<<s.next_cursor<<' '<<s.skipped<<' '<<calls.size()/5;
            for(auto value:calls)std::cout<<' '<<value;
            std::cout<<'|'<<r.message<<'\n';
            auto snapshot=w.export_save();
            std::ofstream out(std::filesystem::path(argv[2])/(std::to_string(step++)+".dat"),std::ios::binary);
            out.write(reinterpret_cast<const char*>(snapshot.data()),snapshot.size());
            if(!out)throw std::runtime_error("snapshot write failed");
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
