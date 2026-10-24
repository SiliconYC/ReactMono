// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only original message mapping, unchanged source included to observe internal name/format helpers.
#include "screens/messages.cpp"
#include <iostream>
#include <sstream>
extern "C" std::uint64_t SDL_GetTicks(){return 0;}
namespace {
std::string unhex(const std::string &s){if(s=="-")return {};std::string r;for(std::size_t i=0;i<s.size();i+=2)r.push_back(char(std::stoi(s.substr(i,2),nullptr,16)));return r;}
std::string hex(std::string_view s){if(s.empty())return "-";constexpr char h[]="0123456789abcdef";std::string r;for(unsigned char c:s){r+=h[c>>4];r+=h[c&15];}return r;}
}
int main(int argc,char **argv){
    if(argc!=2)return 2;
    try{
        using namespace rich4;using namespace native::messages;
        native::Artwork art(argv[1]);World world;std::string line;
        auto p=[](auto v){std::cout<<' '<<static_cast<long long>(v);};
        auto item=[&](const std::optional<Item> &o){p(bool(o));if(!o)return;const auto &x=*o;
            p(x.kind);p(x.focus?static_cast<long long>(*x.focus):-1);p(x.character);p(x.mood);p(x.pictogram);p(x.voice);p(x.minimum_ms);p(x.wait_voice);p(x.box_x);p(x.photo);std::cout<<' '<<hex(x.text)<<' '<<hex(x.title);p(x.rows.size());for(const auto &r:x.rows){p(r.character);p(r.portrait_frame);std::cout<<' '<<hex(r.text);}};
        while(std::getline(std::cin,line)){
            std::istringstream in(line);char op;in>>op;std::vector<std::uint8_t> before;
            if(op!='N')before=world.export_save();
            std::cout<<0;
            if(op=='N'){
                unsigned map,ch;in>>map>>ch;NewGameOptions opt;opt.map_id=map%4;opt.stage_id=map/4;
                for(unsigned i=0;i<4;++i)opt.players[i].character=(ch+i*3)%12;
                world=World::from_map_resource(art.archive('m').decode(map*2+1),opt);
            }else if(op=='E'){
                GameEvent e;int player,announcement,id,players,category,table,slot,mood;in>>player>>announcement>>id>>e.amount>>e.property>>e.subject>>e.second_subject>>e.company>>e.value>>players;e.announcement_id=id;e.players=players;
                for(auto &v:e.player_amounts)in>>v;in>>category>>table>>slot>>mood;
                e.player=player;e.announcement=Announcement(announcement);if(category>=0)e.voice_category=category;e.speech_table=SpeechTable(table);e.speech_slot=slot;e.speech_mood=mood;
                item(from_event(e,world));
            }else if(op=='B'){
                unsigned ch,category;int focus;in>>ch>>category>>focus;item(speech_bubble(ch,category,focus<0?std::nullopt:std::optional<std::size_t>(focus)));
            }else if(op=='T'){
                unsigned ch,table,slot,mood;int focus;in>>ch>>table>>slot>>mood>>focus;item(item_speech_bubble(ch,SpeechTable(table),slot,mood,focus<0?std::nullopt:std::optional<std::size_t>(focus)));
            }else if(op=='V'){
                int type,index;in>>type>>index;
                std::string r=type==0?stock_name(world,index):type==1?property_name(world,index):type==2?company_name(world,index):player_name(world,index);std::cout<<' '<<hex(r);
            }else if(op=='S'){
                unsigned type,value;in>>type>>value;std::cout<<' '<<hex(subject_name(world,CardTarget{CardTargetKind(type),std::uint16_t(value)}));
            }else if(op=='D'){
                GameDecision d;unsigned kind,player,n;in>>kind>>player>>d.land_id>>d.amount>>n;d.kind=DecisionKind(kind);d.player=player;
                while(n--){DecisionOption o;int k;unsigned v;std::string label;in>>o.value>>k>>v>>label;o.label=unhex(label);if(k>=0)o.subject=CardTarget{CardTargetKind(k),std::uint16_t(v)};d.options.push_back(o);}
                const auto r=localized(d,world);p(is_yes_no(d));std::cout<<' '<<hex(yes_no_question(d,world))<<' '<<hex(r.prompt);p(r.options.size());
                for(const auto &o:r.options){p(o.value);std::cout<<' '<<hex(o.label);p(o.subject?static_cast<int>(o.subject->kind):-1);p(o.subject?o.subject->value:0);}
            }else if(op=='F'){unsigned type;in>>type;world.facilities.at(1).facility_type=type;
            }else if(op=='Q'){
                unsigned slot,days;in>>slot>>days;world.players.at(slot).status.days_disappearing=days;
            }else return 3;
            if(op!='N'&&op!='Q'&&op!='F'&&before!=world.export_save())throw std::runtime_error("message mapping modified world");
            std::cout<<'\n';std::cout.flush();
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
