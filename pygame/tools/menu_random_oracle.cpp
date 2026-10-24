// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: menus.cpp uses raw std::mt19937 outputs modulo available characters.
#include <cstdint>
#include <iostream>
#include <random>
int main(){std::ios::sync_with_stdio(false);std::uint32_t seed;unsigned count;while(std::cin>>seed>>count){std::mt19937 r(seed);for(unsigned i=0;i<count;++i)std::cout<<r()<<' ';std::cout<<'\n'<<r<<'\n';}}
