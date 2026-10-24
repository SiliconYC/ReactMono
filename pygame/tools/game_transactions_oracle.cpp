// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only fixed implementation probes (-fno-access-control); no reference source edits.
#include "game.cpp"
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <sstream>
#include "game_actor_probes.hpp"
#include "game_probe_output.hpp"

int main(int argc,char **argv) {
    if(argc!=4&&argc!=5)return 2;
    try {
        using namespace rich4;
        const bool finance=argc==5;
        const bool actors=finance&&std::string(argv[4])=="actors";
        std::vector<long long> actor_values;
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
            g.card_picture_shown=false;g.animation.reset();actor_values.clear();
            if(finance){g.winner.reset();g.resume_movement=g.bank_resume_encounter=false;g.remaining=0;}
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
                    World *held=&g.world;
                    auto action=[&,cost,depth,flavor,held]{
                        for(int i=1;i<=depth;++i){
                            auto &p=(flavor==5?held->players:g.world.players)[g.actor()].state;
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
                else if(op=='S'){
                    auto &p=g.world.players.at(n.at(0));p.status.cumulative_spending=123;p.status.hostility={1,2,3,4};p.status.init_cash_ratio=73;
                    auto *held=&p.status;auto *array=&p.status.hostility;
                    g.world.clear_bankrupt_player_fields(n.at(0));
                    values={held==&p.status,array==&p.status.hostility,held->cumulative_spending,held->init_cash_ratio};
                    for(auto v:*array)values.push_back(v);
                }
                else if(op=='d'){g.events.clear();g.effects.clear();}
                else if(finance&&op=='P'){
                    auto &p=g.world.players.at(n.at(0)).state;
                    p.cash=n.at(1);p.bank_balance=n.at(2);p.loan=n.at(3);p.special_finance=n.at(4);p.controller_flags=n.at(5);
                }else if(finance&&op=='T'){
                    auto &p=g.world.players.at(n.at(0)).status;
                    p.days_bank_no_loans=n.at(1);p.days_rejected_by_bank=n.at(2);p.loan_due_date=n.at(3);p.days_assurance=n.at(4);p.init_cash_ratio=n.at(5);p.loan_ratio=n.at(6);p.cumulative_spending=n.at(7);p.cumulative_income=n.at(8);p.total_winter_sleep_days=n.at(9);p.god_luck_modifier=n.at(10);p.allied_days=n.at(11);p.allied_player=n.at(12);
                    for(unsigned i=0;i<4;++i)p.hostility[i]=n.at(13+i);
                }else if(finance&&op=='C'){
                    auto &p=g.world.commercials.at(n.at(0));p.commerce_type=n.at(1);p.owner_code=n.at(2);p.funds=n.at(3);p.funds_change=n.at(4);
                }else if(finance&&op=='H'){
                    g.world.header.current_player=n.at(0);g.world.header.price_index=n.at(1);g.world.header.initial_fund=n.at(2);g.world.header.date={std::uint8_t(n.at(5)),std::uint8_t(n.at(4)),std::uint16_t(n.at(3))};g.world.lease_mode=n.at(6);
                }else if(finance&&op=='L'){
                    auto code=n.at(0);if(code>=4000){auto &p=g.world.facilities.at(code-4000);p.owner_code=n.at(1);p.level=n.at(2);p.temporary_state=n.at(3);p.expired_date=n.at(4);}else{auto &p=g.world.lands.at(code-2000);p.economy.owner_code=n.at(1);p.economy.level=n.at(2);p.temporary_state=n.at(3);p.expired_date=n.at(4);}
                }else if(finance&&op=='K')g.world.players.at(n.at(0)).stocks.at(n.at(1)).amount=n.at(2);
                else if(finance&&op=='J')g.world.stocks.at(n.at(0)).flags_4=n.at(1);
                else if(finance&&op=='N')g.world.nodes.at(g.player().node_id).type_and_index=n.at(0);
                else if(finance&&op=='F'){
                    switch(n.at(0)){
                    case 0:values={g.pay(n.at(1),n.at(2),n.at(3),n.at(4))};break;
                    case 1:g.update_hostility(n.at(1),n.at(2),n.at(3));break;
                    case 2:values={g.wealth(n.at(1))};break;
                    case 3:values={g.check_game_end()};break;
                    case 4:g.bankrupt(n.at(1));break;
                    case 5:g.insure(n.at(1),n.at(2));break;
                    case 6:g.collect_bank_debt(n.at(1),n.at(2));break;
                    case 7:g.collect_due_loan();break;
                    case 8:g.reconcile_financing(n.at(1));break;
                    case 9:g.set_loan_due_date(n.at(1));break;
                    case 10:values={g.borrow(n.at(1))};break;
                    case 11:values={g.repay(n.at(1),n.at(2))};break;
                    case 12:g.ai_bank_loan();break;
                    case 13:values={g.owns_current_bank(),g.financing_limit()};break;
                    case 14:values={g.change_financing(n.at(1),n.at(2))};break;
                    case 15:g.open_bank(n.at(1));break;
                    case 16:g.leave_bank();break;
                    case 17:g.update_price_index();break;
                    case 18:g.pay_dividends();break;
                    case 19:g.close_month();break;
                    case 20:values={g.lease_expiry()};break;
                    case 21:g.expire_properties();break;
                    case 22:g.pay_toll(n.at(1),n.at(2),n.at(3),n.at(4)<0?std::nullopt:std::optional<std::size_t>(n.at(4)),n.at(5),n.at(6),n.at(7),n.at(8));break;
                    default:return 3;
                    }
                }
                else if(actors&&op=='B'){
                    actor_values.clear();g.run_rule([&g,n,&actor_values]{actor_probe(g,n,actor_values);},true,false);
                }else if(actors&&actor_prepare(g,op,n)){}
                else return 3;
            }catch(const std::out_of_range &){status=2;}
            catch(const std::invalid_argument &){status=1;}
            dump_game_probe(g,status,values,successes,finance,actors,actor_values);
            auto data=g.world.export_save();std::ofstream out(std::filesystem::path(argv[2])/(std::to_string(step++)+".dat"),std::ios::binary);out.write(reinterpret_cast<const char*>(data.data()),data.size());if(!out)return 5;
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
