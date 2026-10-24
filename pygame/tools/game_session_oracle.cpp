// SPDX-License-Identifier: GPL-3.0-or-later
// Public GameSession operations against the unedited pinned source; binary states are test-only.
#include "game.cpp"
#include "rich4/assets.hpp"
#include <iomanip>
#include <iostream>
#include <iterator>
#include <sstream>
#include "game_probe_output.hpp"

static void target(const std::optional<rich4::CardTarget> &v) {
    std::cout<<' '<<bool(v);if(v)std::cout<<' '<<int(v->kind)<<' '<<v->value;
}
static void ai(const std::optional<rich4::AiSettings> &v) {
    std::cout<<' '<<bool(v);if(v)std::cout<<' '<<v->autopilot<<' '<<unsigned(v->card_strategy)<<' '<<unsigned(v->personality)<<' '<<unsigned(v->cash_ratio)<<' '<<unsigned(v->stock_ratio);
}
static void extra(rich4::GameSession::Impl &g) {
    std::cout<<g.faces.size();for(auto v:g.faces)std::cout<<' '<<unsigned(v);
    std::cout<<' '<<g.remaining<<' '<<g.next_node<<' '<<g.days<<' '<<(g.winner?int(*g.winner):-1)<<' '<<g.resume_movement<<' '<<g.bank_resume_encounter;
    std::cout<<' '<<g.roulette_cursor<<' '<<g.roulette_elapsed<<' '<<g.roulette_kind<<' '<<g.roulette_facility<<' '<<g.rescue_hospital<<' '<<g.magic_category<<' '<<g.last_action_accepted<<' '<<int(g.unsupported_resume);
    std::cout<<' '<<bool(g.forced_roll);if(g.forced_roll)std::cout<<' '<<*g.forced_roll;
    std::cout<<' '<<g.mine_pending<<' '<<g.card_picture_shown<<' '<<g.property_pending<<' '<<g.purchased_property<<' '<<g.property_landing<<' '<<g.interactive_mini_games;
    target(g.chosen_card_target);std::cout<<' '<<bool(g.card_in_use);if(g.card_in_use){std::cout<<' '<<unsigned(g.card_in_use->card_id);target(g.card_in_use->target);target(g.card_in_use->choice);}
    std::cout<<' '<<bool(g.animation);if(g.animation){auto &a=*g.animation;std::cout<<' '<<a.player<<' '<<a.from_x<<' '<<a.from_y<<' '<<a.to_x<<' '<<a.to_y<<' '<<a.elapsed_ms<<' '<<a.duration_ms;}
    std::cout<<' '<<bool(g.shop)<<' '<<g.shop_property;if(g.shop){auto &s=*g.shop;std::cout<<' '<<s.cards.size();for(auto v:s.cards)std::cout<<' '<<unsigned(v);std::cout<<' '<<s.tools.size();for(auto v:s.tools)std::cout<<' '<<unsigned(v);std::cout<<' '<<s.revenue<<' '<<unsigned(s.gift_card)<<' '<<unsigned(s.gift_tool)<<' '<<s.closed;}
    std::cout<<' '<<bool(g.money_spinner)<<' '<<g.spinner_random.state()<<' '<<g.spinner_elapsed;
    if(g.money_spinner){auto &s=*g.money_spinner;for(auto v:s.digits_)std::cout<<' '<<unsigned(v);std::cout<<' '<<s.omitted_digit_<<' '<<s.phase_<<' '<<s.frames_<<' '<<s.slowing_period_<<' '<<s.slowing_elapsed_<<' '<<s.last_slowing_digit_;}
    for(auto &s:g.pending_ai_settings)ai(s);
    std::cout<<' '<<g.world.has_initial_random_state()<<' '<<g.world.initial_random_state();
    for(auto &w:g.previous_turn){std::cout<<' '<<bool(w);if(w)std::cout<<' '<<w->has_initial_random_state()<<' '<<w->initial_random_state();}
    std::cout<<'\n';
}
static void bytes(const std::vector<std::uint8_t> &v) {
    const std::uint32_t size=v.size();for(unsigned i=0;i<4;++i)std::cout.put(static_cast<char>(size>>(i*8)));
    std::cout.write(reinterpret_cast<const char*>(v.data()),v.size());
}
int main(int argc,char **argv) {
    if(argc!=4)return 2;
    try {
        using namespace rich4;
        const unsigned id=std::stoul(argv[2]),seed=std::stoul(argv[3]);
        assets::Archive archive(argv[1]);NewGameOptions opt;opt.map_id=id%4;opt.stage_id=id/4;opt.random_seed=seed;
        GameSession game(World::from_map_resource(archive.decode(id*2+1),opt),seed);
        std::string line;
        while(std::getline(std::cin,line)) {
            std::istringstream in(line);std::string op;in>>op;
            std::vector<long long> n{std::istream_iterator<long long>(in),{}};
            int status=0;std::vector<long long> values;
            try {
                if(op=="i"){}
                else if(op=="t")game.tick(n.at(0));
                else if(op=="a")values={game.set_ai_settings(n.at(0),AiSettings{bool(n.at(1)),std::uint8_t(n.at(2)),std::uint8_t(n.at(3)),std::uint8_t(n.at(4)),std::uint8_t(n.at(5))})};
                else if(op=="r")values={game.roll_dice()};
                else if(op=="c")values={game.respond(n.at(0),n.at(1))};
                else if(op=="d"){auto e=game.drain_events();auto f=game.drain_effects();values={static_cast<long long>(e.size()),static_cast<long long>(f.size())};}
                else if(op=="v")game.set_camera_rotation(n.at(0));
                else if(op=="n")values={game.set_dice_count(n.at(0))};
                else if(op=="u")values={game.use_tool(n.at(0),n.at(1),n.at(2))};
                else if(op=="k"){CardUse u;u.card_id=n.at(0);if(n.at(1)>=0)u.target=CardTarget{CardTargetKind(n.at(1)),std::uint16_t(n.at(2))};if(n.at(3)>=0)u.choice=CardTarget{CardTargetKind(n.at(3)),std::uint16_t(n.at(4))};values={game.use_card(u)};}
                else if(op=="b")values={game.buy_stock(n.at(0),n.at(1))};
                else if(op=="s")values={game.sell_stock(n.at(0),n.at(1))};
                else if(op=="x")game.set_interactive_mini_games(n.at(0));
                else if(op=="q")values={game.submit_mini_game(n.at(0),n.at(1))};
                else if(op=="m")values={game.dismount()};
                else if(op=="g")values={game.can_save()};
                else return 3;
            }catch(const std::out_of_range &){status=2;}
            catch(const std::invalid_argument &){status=1;}
            catch(const std::exception &e){status=3;std::cerr<<op<<": "<<e.what()<<'\n';}
            auto &g=*game.impl_;dump_game_probe(g,status,values);extra(g);bytes(g.world.export_save());
            for(auto &w:g.previous_turn)bytes(w?w->export_save():std::vector<std::uint8_t>{});
            std::cout.flush();
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
