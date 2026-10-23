// SPDX-License-Identifier: GPL-3.0-or-later
// Lossless-codec differential adapter, test-only; input saves stay local.
#include "rich4/save.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <vector>

void write(const std::string &path, const std::vector<std::uint8_t> &bytes) {
    std::ofstream out(path, std::ios::binary);
    out.write(reinterpret_cast<const char *>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
    if (!out) throw std::runtime_error("save oracle output failed");
}
int main(int argc,char **argv) {
    if (argc != 3) return 2;
    try {
        std::ifstream file(argv[1],std::ios::binary);
        if (!file) throw std::runtime_error("input not found");
        std::vector<std::uint8_t> input{std::istreambuf_iterator<char>(file), {}};
        auto save=rich4::SaveFile::decode(input);
        auto h=save.header();
        std::cout<<h.signature<<' '<<unsigned(h.date.day)<<' '<<unsigned(h.date.month)<<' '
            <<h.date.year<<' '<<h.map_id<<' '<<h.stage_id<<' '<<h.player_count<<' '
            <<h.human_player_count<<' '<<h.current_player<<' '<<h.initial_fund<<' '<<h.price_index<<'\n';
        for (unsigned slot=0;slot<h.player_count;++slot) {
            auto p=save.player(slot);
            std::cout<<p.slot<<' '<<p.color<<' '<<p.x<<' '<<p.y<<' '<<p.node_id<<' '<<p.last_node_id<<' '
                <<unsigned(p.direction)<<' '<<unsigned(p.traffic_method)<<' '<<unsigned(p.dice_count)<<' '
                <<unsigned(p.character)<<' '<<unsigned(p.sex)<<' '<<unsigned(p.controller_flags)<<' '
                <<p.cash<<' '<<p.bank_balance<<' '<<p.loan<<' '<<p.special_finance<<' '<<p.points;
            for(auto v:p.cards)std::cout<<' '<<unsigned(v);
            for(auto v:p.tool_amounts)std::cout<<' '<<unsigned(v);
            std::cout<<'\n';
        }
        auto m=save.map_summary();
        std::cout<<m.byte_size;
        for(auto t:{m.nodes,m.lands,m.facilities,m.commercials,m.raw_reserved_table_4})
            std::cout<<' '<<t.count<<' '<<t.byte_offset<<' '<<t.record_bytes;
        std::cout<<'\n';
        for(auto r:save.regions())std::cout<<r.name<<' '<<r.offset<<' '<<r.byte_size<<' '<<static_cast<int>(r.kind)<<'\n';
        write(std::string(argv[2])+".roundtrip.dat",save.encode());
        const std::vector<std::int32_t> values{0,-1,123456789,std::numeric_limits<std::int32_t>::min(),std::numeric_limits<std::int32_t>::max()};
        for(unsigned slot=0;slot<h.player_count;++slot)for(unsigned i=0;i<values.size();++i){
            auto changed=rich4::SaveFile::decode(input);
            changed.set_cash(slot,values[i]);
            write(std::string(argv[2])+"."+std::to_string(slot)+"."+std::to_string(i)+".cash.dat",changed.encode());
            changed.set_bank_balance(slot,values[i]);
            write(std::string(argv[2])+"."+std::to_string(slot)+"."+std::to_string(i)+".bank.dat",changed.encode());
        }
    } catch(const std::exception &error){ std::cerr<<error.what()<<'\n';return 1; }
}
