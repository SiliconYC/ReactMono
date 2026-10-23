// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only callback observer; these hooks do not implement game finance or object respawn.
#include "rich4/special_actors.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>

int main(int argc, char **argv) {
    if (argc != 4) return 2;
    try {
        std::ifstream file(argv[1], std::ios::binary);
        std::vector<std::uint8_t> bytes{std::istreambuf_iterator<char>(file), {}};
        auto w = rich4::World::from_save(rich4::SaveFile::decode(bytes));
        rich4::Random rng(static_cast<std::uint32_t>(std::stoul(argv[3])));
        std::filesystem::create_directories(argv[2]);
        char op;
        unsigned step = 0;
        int slot, node, last, owner, inactive, flags, sleep, walk, stop, slow;
        unsigned nodeflags, code, kind, mask, gameover, mutate, stopped;
        while (std::cin >> op >> slot >> node >> last >> owner >> inactive >> flags >> sleep >> walk >> stop >> slow >> nodeflags >> code >> kind >> mask >> gameover >> mutate >> stopped) {
            if (slot >= 4 && slot <= 7) {
                auto &a = w.special_actors[slot - 4];
                a.node_id = node; a.last_node_id = last; a.owner = owner; a.inactive_state = inactive;
                a.flags = flags; a.days_sleeping = sleep; a.days_sleep_walking = walk;
                a.days_stopping = stop; a.days_tortoise_walking = slow;
            }
            if (node >= 0 && static_cast<std::size_t>(node) < w.nodes.size()) {
                w.nodes[node].flags = nodeflags; w.nodes[node].type_and_index = code;
            }
            w.objects[0].kind = kind;
            std::vector<std::int64_t> calls;
            auto record = [&](int k, int a=0, int b=0, int c=0, int d=0) {calls.insert(calls.end(), {k,a,b,c,d});};
            rich4::special_actors::Callbacks cb;
            if (mask & 1) cb.pay = [&](auto a, auto b, auto c, auto d) {record(1,a,b,c,d);};
            if (mask & 2) cb.remove_object = [&](auto id) {
                record(2,id);
                if (mutate && node >= 0 && static_cast<std::size_t>(node) < w.nodes.size()) w.nodes[node].flags &= 0xff00ffffU;
            };
            auto confine = [&](int k, auto a, auto b) {record(k,a,b); if (mutate) w.special_actors.at(a-4).inactive_state = 2;};
            if (mask & 4) cb.prison = [&](auto a, auto b) {confine(3,a,b);};
            if (mask & 8) cb.hospital = [&](auto a, auto b) {confine(4,a,b);};
            if (mask & 16) cb.voice = [&](auto a, auto b) {record(5,a,b);};
            unsigned overcalls = 0;
            if (mask & 32) cb.game_over = [&] {bool over = overcalls++ >= gameover; record(6,over); return over;};
            if (mask & 64) cb.after_step = [&](auto a, auto b) {record(7,a,b); if (mutate && b % 17 == 0) w.special_actors.at(a-4).inactive_state = 1;};
            int status = 0, returned = 0;
            rich4::special_actors::Result r;
            try {
                using namespace rich4::special_actors;
                if (op == 'm') returned = move_one_step(w,rng,slot);
                else if (op == 'i') r = interact(w,rng,slot,stopped,cb);
                else if (op == 't') r = turn(w,rng,slot,cb);
                else if (op == 'a') {if(slot < 4 || slot > 7) throw std::out_of_range("slot"); age_status(w.special_actors.at(slot-4));}
                else return 3;
            } catch (const std::out_of_range &) {status = 2;}
            catch (const std::invalid_argument &) {status = 1;}
            std::cout << status << ' ' << rng.state() << ' ' << r.supported << ' ' << r.stop_movement << ' ' << r.planned_steps << ' ' << r.moved_steps << ' ' << returned << ' ' << r.effects.size();
            for (auto &e : r.effects) std::cout << ' ' << static_cast<int>(e.kind) << ' ' << e.actor << ' ' << e.target << ' ' << e.amount << ' ' << e.node;
            std::cout << ' ' << calls.size()/5;
            for (auto n : calls) std::cout << ' ' << n;
            std::cout << '|' << r.message << '\n';
            auto snapshot = w.export_save();
            std::ofstream out(std::filesystem::path(argv[2]) / (std::to_string(step++)+".dat"), std::ios::binary);
            out.write(reinterpret_cast<const char *>(snapshot.data()), snapshot.size());
            if (!out) throw std::runtime_error("snapshot write failed");
        }
    } catch (const std::exception &e) {std::cerr << e.what() << '\n'; return 1;}
}
