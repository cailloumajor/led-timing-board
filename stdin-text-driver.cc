#include "graphics.h"
#include "led-matrix.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

using namespace rgb_matrix;

static int usage(const char* progname)
{
    fprintf(stderr, "usage: %s [options]\n", progname);
    fprintf(stderr,
        "Reads text from stdin and displays it. Empty string: clear screen\n");
    fprintf(stderr, "Options:\n");
    rgb_matrix::PrintMatrixFlags(stderr);
    fprintf(stderr,
        "\t-f <font-file>    : Use given font.\n"
        "\t-C <r,g,b>        : Color. Default 255,255,0\n"
        "\t-B <r,g,b>        : Background-Color. Default 0,0,0\n");
    return 1;
}

static bool parseColor(Color* c, const char* str)
{
    return sscanf(str, "%hhu,%hhu,%hhu", &c->r, &c->g, &c->b) == 3;
}

static bool FullSaturation(const Color& c)
{
    return (c.r == 0 || c.r == 255)
        && (c.g == 0 || c.g == 255)
        && (c.b == 0 || c.b == 255);
}

int main(int argc, char* argv[])
{
    RGBMatrix::Options matrix_options;
    rgb_matrix::RuntimeOptions runtime_opt;
    if (!rgb_matrix::ParseOptionsFromFlags(&argc, &argv,
            &matrix_options, &runtime_opt)) {
        return usage(argv[0]);
    }

    Color color(255, 255, 0);

    const char* bdf_font_file = nullptr;

    int opt;
    while ((opt = getopt(argc, argv, "f:C:")) != -1) {
        switch (opt) {
        case 'f':
            bdf_font_file = strdup(optarg);
            break;
        case 'C':
            if (!parseColor(&color, optarg)) {
                fprintf(stderr, "Invalid color spec: %s\n", optarg);
                return usage(argv[0]);
            }
            break;
        default:
            return usage(argv[0]);
        }
    }

    if (!bdf_font_file) {
        fprintf(stderr, "Need to specify BDF font-file with -f\n");
        return usage(argv[0]);
    }

    // Load font. This needs to be a filename with a bdf bitmap font.
    rgb_matrix::Font font;
    if (!font.LoadFont(bdf_font_file)) {
        fprintf(stderr, "Couldn't load font '%s'\n", bdf_font_file);
        return 1;
    }

    RGBMatrix* canvas = rgb_matrix::CreateMatrixFromOptions(matrix_options,
        runtime_opt);
    if (!canvas) {
        return 1;
    }

    const bool all_extreme_colors = FullSaturation(color);
    if (all_extreme_colors) {
        canvas->SetPWMBits(1);
    }

    const int x_orig = 0;
    const int y_orig = 0;
    int y = y_orig;

    if (isatty(STDIN_FILENO)) {
        // Only give a message if we are interactive. If connected via pipe, be
        // quiet
        printf("Enter lines. Full screen or empty line clears screen.\n"
               "Supports UTF-8. CTRL-D for exit.\n");
    }

    char line[1024];
    while (fgets(line, sizeof(line), stdin)) {
        const size_t last = strlen(line);
        if (last > 0) {
            line[last - 1] = '\0'; // remove newline.
        }
        bool line_empty = strlen(line) == 0;
        if ((y + font.height() > canvas->height()) || line_empty) {
            canvas->Clear();
            y = y_orig;
        }
        if (line_empty) {
            continue;
        }
        // The regular text. Unless we already have filled the background with
        // the outline font, we also fill the background here.
        rgb_matrix::DrawText(
            canvas,
            font,
            x_orig,
            y + font.baseline(),
            color,
            nullptr,
            line,
            0);
        y += font.height();
    }

    // Finished. Shut down the RGB matrix.
    canvas->Clear();
    delete canvas;

    return 0;
}
