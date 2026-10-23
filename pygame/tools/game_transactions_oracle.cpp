// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only fixed implementation probes (-fno-access-control); no reference source edits.
#include "game.cpp"
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <sstream>

int main(int argc,char **argv) {
    if(argc!=4)return 2;
    try {
        using namespace rich4;
        std::ifstream input(argv[1],std::ios::binary);
        std::vector<std::uint8_t> bytes{std::istreambuf_iterator<char>(input),{}};
        const auto base=World::from_save(SaveFile::decode(bytes));
        auto inert=base;for(auto &p:inert.players)p.state.controller_flags=0;
        GameSession::Impl g(inert,0);
        const unsigned seed=std::stoul(argv[3]);
        auto reset=[&]{
            g.world=base;g.random.seed(seed);g.phase=GamePhase::moving;g.phase_elapsed=99;
            g.events.clear();g.effects.clear();g.event_choices.clear();g.choice_random_states.clear();
            g.card_ai_memory={5,6,7};g.pending_continuation={};g.pending_choice_key=0;g.decision.reset();
            g.choice_sequence=99;g.property_pending=g.purchased_property=g.property_landing=false;
            g.costumes={};g.costume_keys={};g.chosen_card_target.reset();g.card_in_use.reset();
            g.card_picture_shown=false;g.animation.reset();
        };
        reset();std::filesystem::create_directories(argv[2]);
        unsigned step=0;int successes=0;
        std::string line;
        while(std::getline(std::cin,line)) {
            std::istringstream in(line);char op;in>>op;
            std::vector<long long> n{std::istream_iterator<long long>(in),{}};
            int status=0;std::vector<long long> values;
            try {
                if(op=='r'){reset();successes=0;}
                else if(op=='s')g.random.seed(n.at(0));
                else if(op=='q'){
                    const int cost=n.at(0),depth=n.at(1),flavor=n.at(2);const bool finish=n.at(3),first=n.at(4);
                    auto action=[&,cost,depth,flavor]{
                        for(int i=1;i<=depth;++i){
                            auto &p=g.world.players[g.actor()].state;
                            p.cash=subtract32(p.cash,add32(cost,i));(void)g.random.next();++g.card_ai_memory.parameter0;
                            g.emit(GameEventKind::notice,"stage"+std::to_string(i),i);
                            g.effect(i%2?EffectKind::monster:EffectKind::explosion,g.actor(),{i,i*2});
                            g.choice_random_states[i]=g.random.state();
                            if(flavor==1&&i==depth)throw UnsupportedRule{"explicit dependency"};
                            if(flavor==2)throw std::invalid_argument("test boundary");
                            if(!g.event_choices.contains(i))throw NeedChoice{GameDecision{DecisionKind::choose_card,g.actor(),0,i,"choose",{{"yes",1},{"no",0}}},std::size_t(i)};
                            p.bank_balance=add32(p.bank_balance,g.event_choices[i]);
                        }
                        if(flavor==3)g.set_phase(GamePhase::rolling);
                        if(flavor==4)g.set_phase(GamePhase::finished);
                    };
                    g.run_rule(action,first,finish,[&]{++successes;});
                }else if(op=='a'){
                    g.event_choices[g.pending_choice_key]=n.at(0);
                    auto continuation=g.pending_continuation;if(continuation)continuation();
                }else if(op=='e')g.emit(GameEventKind(n.at(0)),"explicit",n.at(1));
                else if(op=='f')g.effect(EffectKind(n.at(0)),n.at(1),{int(n.at(2)),int(n.at(3))},n.at(4));
                else if(op=='v')g.amount_voice(n.at(0),n.at(1),n.at(2));
                else if(op=='h')g.absence_voice(n.at(0),n.at(1));
                else if(op=='b')g.speak(n.at(0),SpeechTable(n.at(1)),n.at(2),n.at(3));
                else if(op=='c')g.cue(n.at(0),n.at(1));
                else if(op=='p'){g.property_landing=n.at(0);g.finish_turn();}
                else if(op=='u')g.unsupported("explicit dependency",GamePhase(n.at(0)));
                else if(op=='g'){g.phase=GamePhase(n.at(0));g.phase_elapsed=n.at(1);}
                else if(op=='t'){auto &p=g.world.players.at(n.at(0));p.state.controller_flags=n.at(1);p.state.traffic_method=n.at(2);p.status.days_sleeping=n.at(3);p.status.days_sleep_walking=n.at(4);p.status.days_disappearing=n.at(5);p.status.days_in_hotel=n.at(6);p.status.days_in_prison=n.at(7);p.status.days_in_hospital=n.at(8);p.state.x=n.at(9);p.state.y=n.at(10);}
                else if(op=='i')g.world.header.price_index=n.at(0);
                else if(op=='k'){g.costumes.at(n.at(0))=n.at(1);g.costume_keys.at(n.at(0))=n.at(2);}
                else if(op=='o'){auto a=n.at(0);if(a<0||std::size_t(a)>=g.world.players.size())throw std::out_of_range("actor");values={g.on_board(a),g.costume_key(a)};}
                else if(op=='w')g.refresh_costumes();
                else if(op=='d'){g.events.clear();g.effects.clear();}
                else return 3;
            }catch(const std::out_of_range &){status=2;}
            catch(const std::invalid_argument &){status=1;}
            std::cout<<status<<' '<<g.random.state()<<' '<<int(g.phase)<<' '<<g.phase_elapsed<<' '<<g.pending_choice_key<<' '<<g.choice_sequence<<' '<<successes<<' '<<bool(g.pending_continuation);
            std::cout<<' '<<g.card_ai_memory.parameter0<<' '<<g.card_ai_memory.parameter1<<' '<<g.card_ai_memory.parameter2;
            for(auto v:g.costumes)std::cout<<' '<<unsigned(v);for(auto v:g.costume_keys)std::cout<<' '<<v;
            std::cout<<' '<<g.event_choices.size();for(auto [k,v]:g.event_choices)std::cout<<' '<<k<<' '<<v;
            std::cout<<' '<<g.choice_random_states.size();for(auto [k,v]:g.choice_random_states)std::cout<<' '<<k<<' '<<v;
            std::cout<<' '<<g.events.size();
            for(auto &e:g.events){std::cout<<' '<<int(e.kind)<<' '<<e.player<<' '<<e.amount<<' '<<e.node<<' '<<std::quoted(e.message)<<' '<<bool(e.voice_category);if(e.voice_category)std::cout<<' '<<unsigned(*e.voice_category);std::cout<<' '<<int(e.announcement)<<' '<<unsigned(e.announcement_id)<<' '<<e.property<<' '<<e.subject<<' '<<e.second_subject<<' '<<e.company<<' '<<e.value<<' '<<unsigned(e.players);for(auto v:e.player_amounts)std::cout<<' '<<v;std::cout<<' '<<bool(e.card);if(e.card)std::cout<<' '<<unsigned(*e.card);std::cout<<' '<<int(e.speech_table)<<' '<<unsigned(e.speech_slot)<<' '<<unsigned(e.speech_mood)<<' '<<bool(e.sound);if(e.sound)std::cout<<' '<<unsigned(*e.sound);}
            std::cout<<' '<<g.effects.size();for(auto &e:g.effects){std::cout<<' '<<int(e.kind)<<' '<<e.player<<' '<<e.node<<' '<<e.target.x<<' '<<e.target.y<<' '<<bool(e.from);if(e.from)std::cout<<' '<<e.from->x<<' '<<e.from->y;std::cout<<' '<<unsigned(e.object_kind)<<' '<<e.dice.size();for(auto v:e.dice)std::cout<<' '<<unsigned(v);std::cout<<' '<<e.property<<' '<<e.after_events<<' '<<bool(e.spinner)<<' '<<bool(e.monthly)<<' '<<unsigned(e.previous_level)<<' '<<unsigned(e.previous_type)<<' '<<unsigned(e.direction);if(e.spinner||e.monthly)return 4;}
            std::cout<<' '<<bool(g.decision);if(g.decision){auto &d=*g.decision;std::cout<<' '<<int(d.kind)<<' '<<d.player<<' '<<d.land_id<<' '<<d.amount<<' '<<std::quoted(d.prompt)<<' '<<d.options.size();for(auto &o:d.options){std::cout<<' '<<std::quoted(o.label)<<' '<<o.value<<' '<<bool(o.location)<<' '<<bool(o.subject);if(o.location||o.subject)return 4;}std::cout<<' '<<d.max_amount<<' '<<bool(d.spinner)<<' '<<bool(d.mini_game)<<' '<<unsigned(d.inactive_players)<<' '<<bool(d.victim);if(d.spinner||d.mini_game||d.victim)return 4;}
            std::cout<<' '<<values.size();for(auto v:values)std::cout<<' '<<v;std::cout<<'\n';
            auto data=g.world.export_save();std::ofstream out(std::filesystem::path(argv[2])/(std::to_string(step++)+".dat"),std::ios::binary);out.write(reinterpret_cast<const char*>(data.data()),data.size());if(!out)return 5;
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
