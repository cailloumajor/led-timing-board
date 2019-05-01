#include <algorithm>
#include <cstdio>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

#include "cxxopts/include/cxxopts.hpp"
#include "matrix/include/graphics.h"
#include "matrix/include/led-matrix.h"

int main(int argc, char* argv[])
{
    std::unique_ptr<rgb_matrix::RGBMatrix> canvas;
    rgb_matrix::Font font;
    std::vector<std::string> color_specs;
    std::vector<rgb_matrix::Color> colors;
    size_t nlines;

    cxxopts::Options options(
        "stdin-text-driver",
        "Reads text from stdin and displays it. Empty string clears screen.");

    options.add_options()(
        "f,font", "BDF font file",
        cxxopts::value<std::string>())(
        "C,color", "Text color, one for each line",
        cxxopts::value<std::vector<std::string>>(color_specs))(
        "h,help", "Print help");

    try {
        rgb_matrix::RGBMatrix::Options matrix_options;
        rgb_matrix::RuntimeOptions runtime_options;
        if (!rgb_matrix::ParseOptionsFromFlags(
                &argc, &argv,
                &matrix_options, &runtime_options)) {
            throw std::string("Error parsing matrix options");
        }

        auto result = options.parse(argc, argv);

        if (result.count("help")) {
            std::cout << options.help() << std::endl
                      << "Matrix options:" << std::endl;
            rgb_matrix::PrintMatrixFlags(stdout);
            exit(0);
        }

        if (result.count("font")) {
            const std::string font_filename = result["font"].as<std::string>();
            if (!font.LoadFont(font_filename.data())) {
                throw std::string("Couldn't load font " + font_filename);
            }
        } else {
            throw std::string("Need to specify BDF font-file with '-f'");
        }

        if (result.count("color")) {
            for (std::string cs : result["color"].as<std::vector<std::string>>()) {
                rgb_matrix::Color c;
                if (sscanf(cs.data(), "%hhu,%hhu,%hhu", &c.r, &c.g, &c.b) != 3) {
                    throw std::string("Invalid color spec: " + cs);
                }
                colors.push_back(c);
            }
        }

        canvas.reset(rgb_matrix::CreateMatrixFromOptions(
            matrix_options, runtime_options));
        if (!canvas) {
            throw std::string("Error creating matrix");
        }

        nlines = canvas->height() / font.height();
        if (nlines <= 0) {
            throw std::string("Font height does not fit in matrix height");
        }
        if (colors.size() != nlines) {
            std::ostringstream oss;
            oss << "Number of colors (" << colors.size()
                << ") different than number of lines (" << nlines << ")";
            throw oss.str();
        }
    } catch (cxxopts::OptionParseException const& e) {
        std::cerr << "Error parsing options: " << e.what() << std::endl
                  << std::endl
                  << "Try '" << argv[0] << " --help' for help." << std::endl;
        exit(1);
    } catch (std::string const& error_text) {
        std::cerr << error_text << std::endl
                  << std::endl
                  << "Try '" << argv[0] << " --help' for help." << std::endl;
        exit(1);
    }

    auto full_saturation = [](rgb_matrix::Color c) {
        return (c.r == 0 || c.r == 255)
            && (c.g == 0 || c.g == 255)
            && (c.b == 0 || c.b == 255);
    };
    if (all_of(colors.cbegin(), colors.cend(), full_saturation)) {
        canvas->SetPWMBits(1);
    }

    const int x_orig = 0;
    const int y_orig = 0;
    unsigned int line_index = 0;

    std::string line;
    while (std::getline(std::cin, line)) {
        if (line_index > (nlines - 1) || line.empty()) {
            canvas->Clear();
            line_index = 0;
        }
        if (line.empty()) {
            continue;
        }

        rgb_matrix::DrawText(
            canvas.get(),
            font,
            x_orig,
            y_orig + line_index * font.height(),
            colors[line_index],
            nullptr,
            line.data());

        line_index++;
    }

    return 0;
}
