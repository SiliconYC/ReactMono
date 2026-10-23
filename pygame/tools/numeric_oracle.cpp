// SPDX-License-Identifier: GPL-3.0-or-later
// Software x87 reference adapter, test-only; no original executable is invoked.
#include "rich4/legacy_float.hpp"
#include <bit>
#include <cstdint>
#include <iostream>
using rich4::numeric::Extended;
int main(){
    unsigned op;std::uint64_t a,b,c;
    while(std::cin>>op>>a>>b>>c){
        try{
            auto x=Extended::from(std::bit_cast<double>(a));
            auto y=Extended::from(std::bit_cast<double>(b));
            auto z=Extended::from(std::bit_cast<double>(c));
            Extended v;
            if(op==0)v=(x+y)*z;
            else if(op==1)v=(x-y)/z;
            else if(op==2)v=(x*y)+z;
            else if(op==3)v=(x/y)-z;
            else return 2;
            unsigned single_status=0,double_status=0;
            std::uint32_t single=0;std::uint64_t twice=0;
            try{single=std::bit_cast<std::uint32_t>(v.single());}catch(const std::out_of_range&){single_status=1;}
            try{twice=std::bit_cast<std::uint64_t>(v.double_precision());}catch(const std::out_of_range&){double_status=1;}
            std::cout<<v.significand<<' '<<v.exponent<<' '<<v.negative<<' '<<single_status<<' '
                <<single<<' '<<double_status<<' '<<twice<<' '<<std::bit_cast<std::uint32_t>(v.integer())<<'\n';
        }catch(const std::invalid_argument&){std::cout<<"invalid\n";}
    }
}
