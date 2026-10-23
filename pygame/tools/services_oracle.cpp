// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only services adapter. Hook logs observe call order without substituting a game session.
#include "rich4/services.hpp"
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>

int main(int argc, char **argv) {
    if (argc != 4) return 2;
    try {
        std::ifstream file(argv[1], std::ios::binary);
        if (!file) throw std::runtime_error("input missing");
        std::vector<std::uint8_t> bytes{std::istreambuf_iterator<char>(file), {}};
        auto w = rich4::World::from_save(rich4::SaveFile::decode(bytes));
        rich4::Random rng(static_cast<std::uint32_t>(std::stoul(argv[3])));
        rich4::services::Shop shop;
        std::filesystem::create_directories(argv[2]);
        std::string op;
        unsigned step = 0;
        while (std::cin >> op) {
            int a = 0, b = 0, c = 0, redirect = -2, mask = 0, count = 0;
            std::vector<std::size_t> targets, result;
            if (op == "o" || op == "b" || op == "t" || op == "s") std::cin >> a >> b;
            else if (op == "u") std::cin >> a >> b >> c;
            else if (op == "c" || op == "r" || op == "q" || op == "m" || op == "a") std::cin >> a;
            else if (op == "x") {
                std::cin >> a >> b >> mask >> redirect >> count;
                for (int i = 0; i < count; ++i) {std::size_t p; std::cin >> p; targets.push_back(p);}
            } else return 3;
            if (!std::cin) return 4;
            std::vector<std::array<std::int64_t, 4>> events;
            rich4::services::MagicCallbacks cb;
            auto log = [&](int code, std::int64_t p, std::int64_t q = 0, std::int64_t n = 0) {
                events.push_back({code, p, q, n});
            };
            if (mask & 1) cb.fortune = [&](std::size_t p) {log(0, p);};
            if (mask & 2) cb.defense = [&](std::size_t p) {int r = redirect == -2 ? static_cast<int>(p) : redirect; log(1, p, r); return r;};
            if (mask & 4) cb.hostility = [&](std::size_t p, std::size_t q, std::int32_t n) {log(2, p, q, n);};
            if (mask & 8) cb.prison = [&](std::size_t p, unsigned n) {log(3, p, n);};
            if (mask & 16) cb.hospital = [&](std::size_t p, unsigned n) {log(4, p, n);};
            if (mask & 32) cb.upgrade = [&](std::uint16_t p) {log(5, p);};
            if (mask & 64) cb.downgrade = [&](std::uint16_t p) {log(6, p);};
            if (mask & 128) cb.auction = [&](std::uint16_t p, std::size_t q) {log(7, p, q);};
            if (mask & 256) cb.turn_around = [&](std::size_t p) {log(8, p);};
            int status = 0, value = 0, other = 0;
            try {
                using namespace rich4::services;
                if (op == "o") shop = open_shop(w, rng, a, b);
                else if (op == "b") value = buy_card(w, shop, a, b);
                else if (op == "t") value = buy_tool(w, shop, a, b);
                else if (op == "s") value = sell_card(w, shop, a, b);
                else if (op == "u") value = sell_tool(w, shop, a, b, c);
                else if (op == "c") close_shop(w, shop, a);
                else if (op == "r") value = receive_random_card(w, rng, a);
                else if (op == "q") value = receive_random_tool(w, rng, a);
                else if (op == "m") result = magic_targets(w, a);
                else if (op == "a") {auto choice = choose_magic_ai(w, rng, a); value = choice ? static_cast<int>(choice->category) : -1; other = choice ? static_cast<int>(choice->effect) : -1;}
                else if (op == "x") value = apply_magic(w, rng, a, targets, b, cb);
            } catch (const std::out_of_range &) {status = 2;}
            catch (const std::invalid_argument &) {status = 1;}
            std::cout << status << ' ' << value << ' ' << other << ' ' << rng.state() << ' ' << result.size();
            for (auto n : result) std::cout << ' ' << n;
            std::cout << ' ' << events.size();
            for (auto &e : events) for (auto n : e) std::cout << ' ' << n;
            std::cout << ' ' << shop.revenue << ' ' << unsigned(shop.gift_card) << ' ' << unsigned(shop.gift_tool) << ' ' << shop.closed << ' ' << shop.cards.size();
            for (auto n : shop.cards) std::cout << ' ' << unsigned(n);
            std::cout << ' ' << shop.tools.size();
            for (auto n : shop.tools) std::cout << ' ' << unsigned(n);
            std::cout << '\n';
            const auto snapshot = w.export_save();
            auto path = std::filesystem::path(argv[2]) / (std::to_string(step++) + ".dat");
            std::ofstream out(path, std::ios::binary);
            out.write(reinterpret_cast<const char *>(snapshot.data()), static_cast<std::streamsize>(snapshot.size()));
            if (!out) throw std::runtime_error("snapshot write failed");
        }
    } catch (const std::exception &e) {std::cerr << e.what() << '\n'; return 1;}
}
