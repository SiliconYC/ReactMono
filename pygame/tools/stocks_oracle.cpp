// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only stock API adapter. Snapshots are local temporary DAT files.
#include "rich4/world.hpp"
#include "rich4/stocks.hpp"
#include "rich4/random.hpp"
#include <bit>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <vector>

int main(int argc,char **argv){
    if(argc==2 && std::string(argv[1])=="--prices"){
        std::uint32_t a,b;
        while(std::cin>>a>>b){
            try{std::cout<<std::bit_cast<std::uint32_t>(rich4::stocks::adjusted_price(std::bit_cast<float>(a),std::bit_cast<float>(b)))<<'\n';}
            catch(const std::invalid_argument&){std::cout<<"invalid\n";}
            catch(const std::out_of_range&){std::cout<<"range\n";}
        }
        return 0;
    }
    if(argc!=4)return 2;
    try{
        std::ifstream file(argv[1],std::ios::binary);
        if(!file)throw std::runtime_error("input missing");
        std::vector<std::uint8_t> bytes{std::istreambuf_iterator<char>(file),{}};
        auto w=rich4::World::from_save(rich4::SaveFile::decode(bytes));
        rich4::Random rng(static_cast<std::uint32_t>(std::stoul(argv[3])));
        std::filesystem::create_directories(argv[2]);
        std::string op;unsigned step=0;
        while(std::cin>>op){
            int p=0,s=0,n=0,flag=0;
            if(op=="b"||op=="s")std::cin>>p>>s>>n>>flag;
            else if(op=="o")std::cin>>p>>s;
            else if(op=="n")std::cin>>s>>n>>flag;
            else if(op=="d"||op=="f"||op=="w"||op=="t"||op=="e")std::cin>>n;
            else if(op!="l")return 3;
            if(!std::cin)return 4;
            int status=0;std::int32_t value=0;bool changed=false;
            try{
                if(op=="b"){auto r=rich4::stocks::buy_stock(w,static_cast<std::size_t>(p),static_cast<std::size_t>(s),n,flag!=0);value=r.cost;changed=r.commercial_owner_changed;}
                else if(op=="s"){auto r=rich4::stocks::sell_stock(w,static_cast<std::size_t>(p),static_cast<std::size_t>(s),n,flag!=0);value=r.proceeds;changed=r.commercial_owner_changed;}
                else if(op=="d")value=rich4::stocks::daily_update(w,rng,n!=0);
                else if(op=="l")rich4::stocks::refresh_trade_limits(w,rng);
                else if(op=="f")value=static_cast<std::int32_t>(rich4::stocks::update_stocks(w,static_cast<unsigned>(n)));
                else if(op=="w")value=rich4::stocks::player_wealth(w,static_cast<std::size_t>(n));
                else if(op=="t")value=static_cast<std::int32_t>(rich4::stocks::trend(w,static_cast<std::size_t>(n)));
                else if(op=="o")value=rich4::stocks::update_commercial_owner(w,static_cast<std::size_t>(p),static_cast<std::size_t>(s));
                else if(op=="e")w.news_effect_days=n;
                else if(op=="n"){w.stocks.at(static_cast<std::size_t>(s)).news_movement=static_cast<std::uint8_t>(n);w.stocks.at(static_cast<std::size_t>(s)).suspension_days=static_cast<std::uint8_t>(flag);}
            }catch(const std::out_of_range&){status=2;}
            catch(const std::invalid_argument&){status=1;}
            std::cout<<status<<' '<<value<<' '<<changed<<' '<<rng.state()<<'\n';
            auto snapshot=w.export_save();
            auto path=std::filesystem::path(argv[2])/(std::to_string(step++)+".dat");
            std::ofstream out(path,std::ios::binary);out.write(reinterpret_cast<const char*>(snapshot.data()),static_cast<std::streamsize>(snapshot.size()));
            if(!out)throw std::runtime_error("snapshot write failed");
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
