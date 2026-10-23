// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only adapter for the pinned C++ core. Never linked into the Python runtime.
#include "rich4/assets.hpp"
#include "rich4/flc.hpp"
#include "rich4/graphics.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <string>

namespace {
void write(const std::filesystem::path &path, const std::vector<std::uint8_t> &bytes) {
    std::ofstream out(path, std::ios::binary);
    out.write(reinterpret_cast<const char *>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
    if (!out) throw std::runtime_error("oracle write failed");
}
void image(const std::filesystem::path &path, const rich4::graphics::Image &image) {
    std::vector<std::uint8_t> result;
    const auto word = [&](std::uint32_t value, int size) {
        for (int i = 0; i < size; ++i) result.push_back(static_cast<std::uint8_t>(value >> (i * 8)));
    };
    for (int value : {image.width, image.height, image.origin_x, image.origin_y})
        word(static_cast<std::uint32_t>(value), 4);
    word(static_cast<std::uint32_t>(image.opaque_pixels.size()), 4);
    for (auto value : image.pixels) word(value, 2);
    result.insert(result.end(), image.opaque_pixels.begin(), image.opaque_pixels.end());
    write(path, result);
}
}
int main(int argc, char **argv) {
    if (argc != 3) return 2;
    try {
        const rich4::assets::Archive archive(argv[1]);
        const std::filesystem::path directory(argv[2]);
        std::filesystem::create_directories(directory);
        for (std::size_t i = 0; i < archive.size(); ++i) {
            auto data = archive.decode(i);
            auto base = directory / std::to_string(i);
            write(base.string() + ".bin", data);
            if (data.size() >= 4 && data[0] == 'S' && data[3] == 0 &&
                ((data[1] == 'P' && data[2] == 'R') || (data[1] == 'M' && data[2] == 'P'))) {
                const auto graphics = rich4::assets::parse_graphics(data);
                if (graphics.entries.empty()) continue;
                for (auto f : std::set<std::size_t>{0, graphics.entries.size() - 1}) {
                    auto frame = rich4::graphics::decode_frame(data, f);
                    auto path = base.string() + "-" + std::to_string(f);
                    image(path + ".image", frame);
                    rich4::graphics::write_ppm(frame, path + ".ppm");
                }
            } else if (rich4::flc::is_flc(data)) {
                rich4::flc::Decoder movie(std::move(data));
                while (movie.next()) {
                    auto f = movie.decoded_frames() - 1;
                    if (f == 0 || f + 1 == movie.frame_count())
                        image(base.string() + "-flc-" + std::to_string(f) + ".image", movie.image());
                }
                if (movie.decoded_frames() != movie.frame_count())
                    throw std::runtime_error("incomplete FLC");
            }
        }
        std::cout << archive.size() << '\n';
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
