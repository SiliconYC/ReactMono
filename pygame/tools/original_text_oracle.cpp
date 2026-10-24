// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: emit fixed upstream table values to a local pipe; no commercial text is copied here.
#include <array>
#include <cstdint>
#include <iostream>
#include <string_view>
#include "screens/voices.hpp"
struct Line { std::uint16_t voice; std::string_view text; };
#include "screens/message_strings.inc"
static void emit(char kind, int character, int slot, int voice, std::string_view text) {
    static constexpr char hex[] = "0123456789abcdef";
    std::cout << kind << ' ' << character << ' ' << slot << ' ' << voice << ' ';
    if (text.empty()) std::cout << '-';
    for (unsigned char c : text) std::cout << hex[c >> 4] << hex[c & 15];
    std::cout << '\n';
}
int main() {
    for (int c = 0; c < 12; ++c) {
        for (int s = 0; s < 27; ++s) emit('E', c, s, 1050 + c * 27 + s, event_lines[c][s]);
        for (int s = 0; s < 26; ++s) emit('T', c, s, tool_lines[c][s].voice, tool_lines[c][s].text);
        for (int s = 0; s < 90; ++s) emit('C', c, s, card_lines[c][s].voice, card_lines[c][s].text);
    }
    for (int i = 0; i < 36; ++i) emit('N', 0, i, 149 + i, news_bodies[i]);
    for (int i = 0; i < 49; ++i) emit('F', 0, i, 185 + i, fortune_bodies[i]);
    for (int i = 0; i < 12; ++i) emit('G', 0, i, -1, god_arrivals[i]);
    for (const auto &line : rich4::native::voices::clerk_lines) emit('V', 0, line.voice, line.voice, line.text);
}
