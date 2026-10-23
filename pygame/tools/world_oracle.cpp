// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only value traversal of the pinned C++ World, independent of Python layouts.
#include "rich4/world.hpp"
#include "rich4/assets.hpp"
#include "rich4/world_validation.hpp"
#include <limits>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <type_traits>
#include <vector>

template<class T> void emit(const T &v);
void emit(const rich4::SaveHeader &v) {
    emit(v.signature);emit(v.date.day);emit(v.date.month);emit(v.date.year);emit(v.map_id);
    emit(v.stage_id);emit(v.player_count);emit(v.human_player_count);emit(v.current_player);
    emit(v.initial_fund);emit(v.price_index);
}
void emit(const rich4::PlayerState &v) {
    emit(v.slot);emit(v.color);emit(v.x);emit(v.y);emit(v.node_id);emit(v.last_node_id);
    emit(v.direction);emit(v.traffic_method);emit(v.dice_count);emit(v.character);emit(v.sex);
    emit(v.controller_flags);emit(v.cash);emit(v.bank_balance);emit(v.loan);emit(v.special_finance);
    emit(v.points);emit(v.cards);emit(v.tool_amounts);
}
void emit(const rich4::PlayerStatus &v) {
    emit(v.card_strategy);emit(v.rescue_strategy);emit(v.loan_ratio);emit(v.init_cash_ratio);
    emit(v.stock_investment_ratio);emit(v.saved_direction);emit(v.loan_due_date);
    emit(v.days_in_hotel);emit(v.days_disappearing);emit(v.days_in_prison);emit(v.days_in_hospital);
    emit(v.days_sleeping);emit(v.days_sleep_walking);emit(v.days_stopping);emit(v.days_tortoise_walking);
    emit(v.days_rejected_by_bank);emit(v.days_bank_no_loans);emit(v.allied_days);emit(v.days_assurance);
    emit(v.god_info);emit(v.attached_bomb);emit(v.allied_player);emit(v.total_winter_sleep_days);
    emit(v.god_luck_modifier);emit(v.money_fortune_modifier);emit(v.other_fortune_modifier);emit(v.facility_id);
    emit(v.hostility);emit(v.cumulative_spending);emit(v.cumulative_income);
    emit(v.flags_100);emit(v.flags_101);emit(v.flags_102);emit(v.flags_103);
}
void emit(const rich4::StockHolding &v){emit(v.amount);emit(v.raw_cost_basis);}
void emit(const rich4::WorldPlayer &v){emit(v.state);emit(v.status);emit(v.stocks);}
void emit(const rich4::LandEconomyRecord &v){emit(v.street_name);emit(v.chain_store);emit(v.owner_code);emit(v.level);emit(v.toll_by_level);}
void emit(const rich4::MapNode &v){emit(v.id);emit(v.x);emit(v.y);emit(v.neighbors);emit(v.type_and_index);emit(v.ground_sprite);emit(v.flags);emit(v.name);}
void emit(const rich4::Land &v){emit(v.id);emit(v.x);emit(v.y);emit(v.economy);emit(v.temporary_state);emit(v.direction);emit(v.price_per_level);emit(v.land_price);emit(v.removed_building);emit(v.expired_date);}
void emit(const rich4::Facility &v){emit(v.id);emit(v.x);emit(v.y);emit(v.name);emit(v.facility_type);emit(v.owner_code);emit(v.level);emit(v.direction);emit(v.temporary_state);emit(v.flags_30);emit(v.land_price);emit(v.toll_by_level);emit(v.removed_building);emit(v.expired_date);}
void emit(const rich4::Commercial &v){emit(v.id);emit(v.x);emit(v.y);emit(v.owner_code);emit(v.commerce_type);emit(v.direction);emit(v.sprite_index);emit(v.toll_fee);emit(v.stock_index);emit(v.funds);emit(v.funds_change);emit(v.shares_remaining);emit(v.shareholder_order);emit(v.valuation);emit(v.name);}
void emit(const rich4::Landscape &v){emit(v.id);emit(v.x);emit(v.y);emit(v.direction);emit(v.sprite_index);emit(v.name);}
void emit(const rich4::SpecialActor &v){emit(v.x);emit(v.y);emit(v.node_id);emit(v.last_node_id);emit(v.owner);emit(v.direction);emit(v.inactive_state);emit(v.flags);emit(v.days_sleeping);emit(v.days_sleep_walking);emit(v.days_stopping);emit(v.days_tortoise_walking);}
void emit(const rich4::MapObject &v){emit(v.kind);emit(v.direction);emit(v.node_id);emit(v.remaining_days);emit(v.attached_player);emit(v.animation_remaining);emit(v.animation_step);emit(v.motion_bits);}
void emit(const rich4::StockState &v){emit(v.flags_4);emit(v.suspension_days);emit(v.news_movement);emit(v.shares_available);emit(v.flags_10);emit(v.float_bits);emit(v.raw_32);}
void emit(const rich4::TradeOffer &v){emit(v.kind);emit(v.flags);emit(v.item);emit(v.price);emit(v.quantity);emit(v.property_type);emit(v.property_level);}
template<class T> void emit(const T &v) {
    if constexpr(std::is_arithmetic_v<T>) std::cout<<+v<<' ';
    else if constexpr(std::is_enum_v<T>) emit(static_cast<std::underlying_type_t<T>>(v));
    else if constexpr(std::is_same_v<T,std::string>) { emit(v.size());for(unsigned char c:v)emit(c); }
    else for(const auto &e:v)emit(e);
}
void dump(const rich4::World &w) {
    emit(w.header);emit(w.players);emit(w.nodes);emit(w.lands);emit(w.facilities);emit(w.commercials);emit(w.landscapes);
    emit(w.card_supply);emit(w.tool_supply);emit(w.news_deck);emit(w.fortune_deck);emit(w.news_cursor);emit(w.fortune_cursor);
    emit(w.prison_roster);emit(w.hospital_roster);emit(w.special_actors);emit(w.objects);emit(w.lottery_tickets);
    emit(w.stocks);emit(w.offers);emit(w.stock_history_bits);emit(w.stock_history_cursor);emit(w.stock_market_index);
    emit(w.stock_market_movement_bits);emit(w.public_fund);emit(w.news_effect_days);emit(w.lease_mode);
    emit(w.camera_rotation);emit(w.round_counter);emit(w.month_counter);emit(w.initial_random_state());emit(w.has_initial_random_state());
    try { rich4::validate_playable_world(w);emit(1); }
    catch(const std::invalid_argument &e) { emit(0);std::cerr<<e.what()<<'\n'; }
    std::cout<<'\n';
}
void write(const std::string &path,const std::vector<std::uint8_t> &bytes){
    std::ofstream out(path,std::ios::binary);out.write(reinterpret_cast<const char*>(bytes.data()),static_cast<std::streamsize>(bytes.size()));
    if(!out)throw std::runtime_error("world oracle write failed");
}
int main(int argc,char **argv){
    if(argc!=3 && argc!=7)return 2;
    try {
        auto w = [&] {
            if(argc==7){
                if(std::string(argv[1])!="--new")throw std::runtime_error("mode");
                rich4::assets::Archive archive(argv[2]);
                auto id=static_cast<unsigned>(std::stoul(argv[3]));
                rich4::NewGameOptions options;
                options.map_id=static_cast<std::uint16_t>(id%4);
                options.stage_id=static_cast<std::uint16_t>(id/4);
                options.random_seed=static_cast<std::uint32_t>(std::stoul(argv[4]));
                auto variant=std::stoul(argv[5]);
                if(variant==1){options.players={{11,1,1,1},{2,2,2,1}};options.lease_mode=5;}
                else if(variant==2){options.players={{8,2,0,0}};options.initial_fund=123456789;}
                return rich4::World::from_map_resource(archive.decode(id*2+1),options);
            }
            std::ifstream in(argv[1],std::ios::binary);
            if(!in)throw std::runtime_error("input missing");
            std::vector<std::uint8_t> bytes{std::istreambuf_iterator<char>(in),{}};
            return rich4::World::from_save(rich4::SaveFile::decode(bytes));
        }();
        auto output=std::string(argv[argc-1]);
        dump(w);write(output+".roundtrip.dat",w.export_save());
        for(unsigned slot=0;slot<w.players.size();++slot){
            auto changed=w;changed.clear_bankrupt_player_fields(slot);
            write(output+".bankrupt-"+std::to_string(slot)+".dat",changed.export_save());
        }
        w.players[0].state.bank_balance=-123;
        if(w.players.size()>1)w.players[1].status.attached_bomb=3;
        w.stocks[2].float_bits[3]=0x7fc01234;
        w.nodes[1].x=std::numeric_limits<std::int16_t>::min();
        write(output+".edited.dat",w.export_save());
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
