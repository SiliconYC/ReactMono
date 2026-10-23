// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only resumable auction observer. Source engine is never used at Python runtime.
#include "rich4/auction.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <memory>
#include <vector>

int main(int argc, char **argv) {
    if (argc != 7) return 2;
    try {
        std::ifstream file(argv[1], std::ios::binary);
        if (!file) throw std::runtime_error("input missing");
        std::vector<std::uint8_t> bytes{std::istreambuf_iterator<char>(file), {}};
        auto w = rich4::World::from_save(rich4::SaveFile::decode(bytes));
        rich4::Random rng(static_cast<std::uint32_t>(std::stoul(argv[3])));
        std::filesystem::create_directories(argv[2]);
        rich4::AuctionOptions options;
        if (std::string(argv[6]) != "-1") options.lease_interval = static_cast<std::uint32_t>(std::stoul(argv[6]));
        std::unique_ptr<rich4::AuctionSession> auction;
        int status = 0;
        try {
            auction = std::make_unique<rich4::AuctionSession>(w, rng, static_cast<std::uint16_t>(std::stoul(argv[4])), std::stoi(argv[5]), options);
        } catch (const std::out_of_range &) {status = 2;}
        catch (const std::invalid_argument &) {status = 1;}
        unsigned step = 0;
        auto emit = [&](int applied) {
            std::cout << status << ' ' << rng.state();
            if (auction) {
                auto decision = auction->decision();
                const auto &result = auction->result();
                std::cout << ' ' << applied << ' ' << auction->finished() << ' ' << auction->initial_price() << ' ' << auction->price()
                          << ' ' << (result.winner ? static_cast<int>(*result.winner) : -1) << ' ' << result.price << ' ' << result.property;
                for (std::size_t p = 0; p < 5; ++p) {auto limit = auction->ai_limit(p); std::cout << ' ' << (limit ? *limit : std::int64_t{-2147483649});}
                std::cout << ' ' << bool(decision);
                if (decision) {
                    std::cout << ' ' << decision->player << ' ' << decision->price << ' ' << unsigned(decision->inactive) << ' ' << decision->actions.size();
                    for (auto action : decision->actions) std::cout << ' ' << static_cast<unsigned>(action);
                }
            }
            std::cout << '\n';
            const auto snapshot = w.export_save();
            std::ofstream out(std::filesystem::path(argv[2]) / (std::to_string(step++) + ".dat"), std::ios::binary);
            out.write(reinterpret_cast<const char *>(snapshot.data()), static_cast<std::streamsize>(snapshot.size()));
            if (!out) throw std::runtime_error("snapshot write failed");
        };
        emit(-1);
        if (!auction) return 0;
        std::string op;
        while (std::cin >> op) {
            int applied;
            if (op == "t") applied = auction->tick();
            else if (op == "b") {unsigned code; std::cin >> code; applied = auction->bid(static_cast<rich4::AuctionAction>(code));}
            else return 3;
            if (!std::cin) return 4;
            emit(applied);
        }
    } catch (const std::exception &e) {std::cerr << e.what() << '\n'; return 1;}
}
