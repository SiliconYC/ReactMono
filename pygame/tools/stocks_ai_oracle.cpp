// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only: include the fixed source to observe private scoring without probability gates.
#include "stocks_ai.cpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <sstream>

int main(int argc,char **argv) {
    if(argc!=4)return 2;
    try {
        using namespace rich4;
        std::ifstream file(argv[1],std::ios::binary);
        std::vector<std::uint8_t> bytes{std::istreambuf_iterator<char>(file),{}};
        auto base=World::from_save(SaveFile::decode(bytes)),w=base;
        Random rng(static_cast<std::uint32_t>(std::stoul(argv[3])));
        std::filesystem::create_directories(argv[2]);
        std::string line;
        unsigned step=0;
        while(std::getline(std::cin,line)) {
            std::istringstream input(line);
            char op;input>>op;
            std::vector<std::int64_t> n{std::istream_iterator<std::int64_t>(input),{}};
            std::vector<std::int64_t> values;
            std::vector<stocks_ai::Trade> trades;
            int status=0;
            try {
                using namespace stocks_ai;
                if(op=='b')trades=buy(w,rng,n.at(0),n.at(1));
                else if(op=='s')trades=sell(w,rng,n.at(0),n.at(1));
                else if(op=='r')w=base;
                else if(op=='t')rng.seed(n.at(0));
                else if(op=='p'){auto &p=w.players.at(n.at(0));p.state.cash=n.at(1);p.state.bank_balance=n.at(2);p.state.loan=n.at(3);p.status.stock_investment_ratio=n.at(4);p.status.loan_due_date=n.at(5);}
                else if(op=='h'){auto &p=w.players.at(n.at(0)).stocks.at(n.at(1));p.amount=n.at(2);p.raw_cost_basis=n.at(3);}
                else if(op=='q'){auto &s=w.stocks.at(n.at(0));s.flags_4=n.at(1);s.shares_available=n.at(2);s.flags_10=n.at(3);s.suspension_days=n.at(4);s.float_bits[0]=n.at(5);s.float_bits[1]=n.at(6);s.float_bits[2]=n.at(7);s.float_bits[4]=n.at(8);}
                else if(op=='c'){auto &c=w.commercials.at(n.at(0));c.funds=n.at(1);c.funds_change=n.at(2);c.valuation=n.at(3);c.owner_code=n.at(4);c.shares_remaining=n.at(5);}
                else if(op=='d'){w.header.date.day=n.at(0);w.header.date.month=n.at(1);w.header.date.year=n.at(2);w.stock_history_cursor=n.at(3);w.month_counter=n.at(4);}
                else if(op=='f'){auto &h=w.stock_history_bits.at(n.at(0));for(unsigned i=0;i<144;++i)h[i]=n.at(1)==1&&i>=138?n.at(3):n.at(1)==2&&i%3==0?(i%2?0x80000000U:0U):n.at(2);}
                else if(op=='o'){std::array<RatedStock,12> entries;for(unsigned i=0;i<12;++i)entries[i]={i,static_cast<std::int32_t>(n.at(i))};original_sort(entries);for(auto e:entries){values.push_back(e.index);values.push_back(e.score);}}
                else if(op=='l')values.push_back(original_day_index(n.at(0)));
                else if(op=='g'){validate(w,0);w.stocks.at(n.at(0));values.push_back(std::bit_cast<std::uint32_t>(history_average(w,n.at(0),n.at(1))));}
                else if(op=='k'){validate(w,n.at(0));values.push_back(holdings_value(w,n.at(0)));}
                else if(op=='a'){validate(w,n.at(0));w.stocks.at(n.at(1));values.push_back(company_buy_score(w,n.at(0),n.at(1)));}
                else if(op=='m'){validate(w,0);w.stocks.at(n.at(0));values.push_back(market_buy_score(w,n.at(0)));}
                else if(op=='e'){validate(w,n.at(0));w.stocks.at(n.at(1));values.push_back(company_sell_score(w,n.at(0),n.at(1),n.at(2)));}
                else if(op=='n'){validate(w,n.at(0));w.stocks.at(n.at(1));values.push_back(market_sell_score(w,n.at(0),n.at(1),n.at(2)));}
                else return 3;
            }catch(const std::out_of_range &){status=2;}
            catch(const std::invalid_argument &){status=1;}
            catch(const SaveError &){status=1;}
            std::cout<<status<<' '<<rng.state()<<' '<<trades.size();
            for(auto t:trades)std::cout<<' '<<t.stock<<' '<<t.quantity<<' '<<t.value<<' '<<t.commercial_owner_changed;
            std::cout<<' '<<values.size();for(auto value:values)std::cout<<' '<<value;
            std::cout<<'\n';
            auto snapshot=w.export_save();
            std::ofstream out(std::filesystem::path(argv[2])/(std::to_string(step++)+".dat"),std::ios::binary);
            out.write(reinterpret_cast<const char*>(snapshot.data()),snapshot.size());
            if(!out)throw std::runtime_error("snapshot write failed");
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
