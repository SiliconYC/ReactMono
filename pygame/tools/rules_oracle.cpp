// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only protocol; every result comes from the pinned C++ core APIs.
#include "rich4/random.hpp"
#include "rich4/calendar.hpp"
#include "rich4/direction.hpp"
#include "rich4/inventory.hpp"
#include "rich4/economy.hpp"
#include <iostream>
#include <string>
#include <vector>

int main() {
    std::string command;
    while (std::cin >> command) {
        if (command == "random") {
            std::uint32_t seed; unsigned count;
            std::cin >> seed >> count;
            rich4::Random rng(seed);
            for (unsigned i = 0; i < count; ++i) std::cout << rng.next() << ' ';
            std::cout << rng.state();
        } else if (command == "direction") {
            std::int32_t x, y; std::cin >> x >> y;
            std::cout << unsigned(rich4::direction::from_delta(x, y));
        } else if (command == "calendar") {
            int day; std::cin >> day;
            auto date = rich4::calendar::from_days(day);
            std::cout << date.year << ' ' << unsigned(date.month) << ' ' << unsigned(date.day)
                << ' ' << unsigned(rich4::calendar::weekday(date)) << ' '
                << rich4::calendar::days_from_1998(date);
        } else if (command == "packed") {
            std::uint32_t date, interval; std::cin >> date >> interval;
            std::cout << rich4::calendar::add_packed_interval(date, interval);
        } else if (command == "inventory") {
            rich4::CardSlots cards{}; rich4::CardSupply supply{}; rich4::CardPrices prices{};
            rich4::ToolAmounts tools{}; rich4::ToolSupply tool_supply{}; rich4::ToolPrices tool_prices{};
            for (auto &p : prices) { unsigned v; std::cin >> v; p = static_cast<std::uint8_t>(v); }
            for (auto &p : supply) { unsigned v; std::cin >> v; p = static_cast<std::uint8_t>(v); }
            for (auto &p : tool_supply) { unsigned v; std::cin >> v; p = static_cast<std::uint8_t>(v); }
            for (auto &p : tool_prices) { unsigned v; std::cin >> v; p = static_cast<std::uint8_t>(v); }
            unsigned count; std::cin >> count;
            for (unsigned i=0;i<count;++i) {
                char op; unsigned id; std::cin >> op >> id;
                std::uint32_t result = 0;
                auto byte = static_cast<std::uint8_t>(id);
                if (op=='r') rich4::receive_card(cards,supply,prices,byte);
                else if (op=='c') result = rich4::consume_card(cards,supply,byte);
                else if (op=='h') result = rich4::drop_half_cards(cards,supply);
                else if (op=='s') result = rich4::sell_all_cards(cards,supply,prices);
                else if (op=='R') result = rich4::receive_tool(tools,tool_supply,byte);
                else if (op=='C') result = rich4::consume_tool(tools,tool_supply,byte);
                else if (op=='S') result = rich4::sell_stored_tools(tools,tool_supply,tool_prices);
                else return 3;
                std::cout << result << ' ';
                for (auto v : cards) std::cout << unsigned(v) << ' ';
                for (auto v : supply) std::cout << unsigned(v) << ' ';
                for (auto v : tools) std::cout << unsigned(v) << ' ';
                for (auto v : tool_supply) std::cout << unsigned(v) << ' ';
            }
        } else if (command == "economy") {
            unsigned count; int owner, price, street;
            std::cin >> count >> owner >> price >> street;
            std::vector<rich4::LandEconomyRecord> lands;
            for (unsigned i=0;i<count;++i) {
                unsigned name, chain, who, level;
                std::cin >> name >> chain >> who >> level;
                rich4::LandEconomyRecord land;
                land.street_name = std::to_string(name);
                land.chain_store = static_cast<std::uint8_t>(chain);
                land.owner_code = static_cast<std::uint8_t>(who);
                land.level = static_cast<std::uint8_t>(level);
                for (auto &t : land.toll_by_level) { unsigned v; std::cin >> v; t = static_cast<std::uint16_t>(v); }
                lands.push_back(land);
            }
            auto text = std::to_string(street);
            std::cout << rich4::chain_store_count(lands,owner) << ' '
                << rich4::land_toll(lands,owner,price,
                    street < 0 ? std::nullopt : std::optional<std::string_view>(text));
        } else return 2;
        if (!std::cin) return 4;
        std::cout << '\n';
    }
}
