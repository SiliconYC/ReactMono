// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only calendar outputs and lottery state snapshots. Never linked by the Python game.
#include "rich4/holidays.hpp"
#include "rich4/lottery.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <vector>

int main(int argc, char **argv) {
    if (argc == 2 && std::string(argv[1]) == "--calendar") {
        int day, table, loan;
        while (std::cin >> day >> table >> loan) {
            const auto d = rich4::calendar::from_days(day);
            const auto map = static_cast<std::uint16_t>(table % 4), stage = static_cast<std::uint16_t>(table / 4);
            const auto lunar = rich4::holidays::lunar_date(d);
            const auto row = rich4::holidays::festival_row(d, map, stage);
            const auto picture = rich4::holidays::festival_picture(d, map, stage);
            const auto party = rich4::holidays::celebration(d, map, stage);
            std::cout << (lunar ? rich4::calendar::pack(*lunar) : 0) << ' '
                      << (row ? static_cast<int>(*row) : -1) << ' '
                      << (picture ? static_cast<int>(*picture) : -1) << ' '
                      << rich4::holidays::is_closed(d, map, stage) << ' ' << bool(party) << ' '
                      << (party ? party->movie : 0) << ' ' << (party ? party->sound : 0) << ' '
                      << (party ? party->music : 0) << ' '
                      << (loan ? rich4::calendar::pack(rich4::holidays::loan_due_date(d, map, stage)) : 0) << '\n';
        }
        return 0;
    }
    if (argc != 4) return 2;
    try {
        std::ifstream file(argv[1], std::ios::binary);
        if (!file) throw std::runtime_error("input missing");
        std::vector<std::uint8_t> bytes{std::istreambuf_iterator<char>(file), {}};
        auto w = rich4::World::from_save(rich4::SaveFile::decode(bytes));
        rich4::Random rng(static_cast<std::uint32_t>(std::stoul(argv[3])));
        std::filesystem::create_directories(argv[2]);
        unsigned step = 0;
        std::string op;
        while (std::cin >> op) {
            int a = 0, b = 0, c = 0;
            std::uint32_t income = 0;
            if (op == "b" || op == "t") std::cin >> a >> b;
            else if (op == "r" || op == "c" || op == "f" || op == "q") std::cin >> a;
            else if (op == "p") std::cin >> a >> b >> c >> income;
            else if (op != "d" && op != "v") return 3;
            if (!std::cin) return 4;
            int status = 0, value = 0;
            rich4::lottery::Draw draw;
            std::vector<std::uint8_t> available;
            try {
                if (op == "b") value = static_cast<int>(rich4::lottery::buy_ticket(w, a, b));
                else if (op == "r") {auto n = rich4::lottery::buy_random_ticket(w, rng, a); value = n ? *n : -1;}
                else if (op == "c") rich4::lottery::discard_player_tickets(w, a);
                else if (op == "d") draw = rich4::lottery::draw(w, rng);
                else if (op == "v") available = rich4::lottery::available_numbers(w);
                else if (op == "t") w.lottery_tickets.at(a) = static_cast<std::uint8_t>(b);
                else if (op == "f") w.public_fund = a;
                else if (op == "p") {auto &p = w.players.at(a); p.state.cash = b; p.state.controller_flags = static_cast<std::uint8_t>(c); p.status.cumulative_income = income;}
                else if (op == "q") value = rich4::lottery::draw_due({static_cast<std::uint8_t>(a), 10, 2026});
            } catch (const rich4::SaveError &) {status = 3;}
            catch (const std::out_of_range &) {status = 2;}
            std::cout << status << ' ' << value << ' ' << unsigned(draw.number) << ' '
                      << (draw.winner ? static_cast<int>(*draw.winner) : -1) << ' ' << draw.payout << ' '
                      << draw.held << ' ' << draw.sold_numbers_only << ' ' << rng.state() << ' ' << available.size();
            for (auto n : available) std::cout << ' ' << unsigned(n);
            std::cout << '\n';
            const auto snapshot = w.export_save();
            std::ofstream out(std::filesystem::path(argv[2]) / (std::to_string(step++) + ".dat"), std::ios::binary);
            out.write(reinterpret_cast<const char *>(snapshot.data()), static_cast<std::streamsize>(snapshot.size()));
            if (!out) throw std::runtime_error("snapshot write failed");
        }
    } catch (const std::exception &e) {std::cerr << e.what() << '\n'; return 1;}
}
