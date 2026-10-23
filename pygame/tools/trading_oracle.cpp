// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only private-market observer. Complete snapshots include preserved record bytes.
#include "rich4/trading.hpp"
#include "rich4/random.hpp"
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
        std::filesystem::create_directories(argv[2]);
        std::string op;
        unsigned step = 0;
        while (std::cin >> op) {
            int a = 0, b = 0, c = 0, d = 0, e = 0;
            std::uint32_t bits = 0;
            if (op == "i" || op == "a") std::cin >> a;
            else if (op == "c") std::cin >> a >> b;
            else if (op == "b") std::cin >> a >> b >> c;
            else if (op == "l") std::cin >> a >> b >> c >> d;
            else if (op == "p") std::cin >> a >> b >> c >> d >> e;
            else if (op == "h") std::cin >> a >> b >> c >> bits;
            else if (op != "q" && op != "n") return 3;
            if (!std::cin) return 4;
            int status = 0;
            rich4::trading::Result result;
            rich4::trading::AiResult ai;
            std::vector<std::int64_t> values;
            auto offer = [&](const rich4::TradeOffer &p) {
                values.insert(values.end(), {static_cast<int>(p.kind), p.flags, p.item, p.price, p.quantity, p.property_type, p.property_level});
            };
            auto quote = [&](const rich4::trading::Quote &q) {values.push_back(q.seller); values.push_back(q.index); offer(q.offer);};
            try {
                using namespace rich4::trading;
                if (op == "i") {auto list = listable_items(w, a); values.push_back(list.size()); for (auto &item : list) values.insert(values.end(), {static_cast<int>(item.kind), item.id, item.maximum_quantity});}
                else if (op == "l") {auto limits = listing_limits(w, a, static_cast<rich4::OfferKind>(b), c, d); values.push_back(bool(limits)); if (limits) values.insert(values.end(), {limits->reference_price, limits->maximum_price});}
                else if (op == "q") {auto list = quotes(w); values.push_back(list.size()); for (auto &q : list) quote(q);}
                else if (op == "p") result = post(w, a, {static_cast<rich4::OfferKind>(b), static_cast<std::uint16_t>(c), d, static_cast<std::uint16_t>(e)});
                else if (op == "c") values.push_back(cancel(w, a, b));
                else if (op == "n") values.push_back(prune(w));
                else if (op == "b") result = buy(w, a, b, c);
                else if (op == "a") ai = ai_turn(w, rng, a);
                else if (op == "h") {auto &s = w.players.at(a).stocks.at(b); s.amount = c; s.raw_cost_basis = bits;}
            } catch (const std::out_of_range &) {status = 2;}
            catch (const std::invalid_argument &) {status = 1;}
            std::cout << status << ' ' << rng.state() << ' ' << result.applied << ' ' << result.commercial_owner_changed
                      << ' ' << ai.removed << ' ' << ai.posted << ' ' << ai.repriced << ' ' << bool(ai.purchased);
            if (ai.purchased) {auto &q = *ai.purchased; auto &p = q.offer; std::cout << ' ' << q.seller << ' ' << q.index << ' ' << static_cast<unsigned>(p.kind) << ' ' << unsigned(p.flags) << ' ' << p.item << ' ' << p.price << ' ' << p.quantity << ' ' << unsigned(p.property_type) << ' ' << unsigned(p.property_level);}
            std::cout << ' ' << values.size();
            for (auto n : values) std::cout << ' ' << n;
            std::cout << '|' << result.message << '\n';
            const auto snapshot = w.export_save();
            std::ofstream out(std::filesystem::path(argv[2]) / (std::to_string(step++) + ".dat"), std::ios::binary);
            out.write(reinterpret_cast<const char *>(snapshot.data()), static_cast<std::streamsize>(snapshot.size()));
            if (!out) throw std::runtime_error("snapshot write failed");
        }
    } catch (const std::exception &e) {std::cerr << e.what() << '\n'; return 1;}
}
