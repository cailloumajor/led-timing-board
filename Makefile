CFLAGS := -O3
override CFLAGS += -Wall -Wextra -Wno-unused-parameter
CXXFLAGS := $(CFLAGS)
LDFLAGS = -lrt -lm -pthread -L$(rgb_libdir) -lrgbmatrix

SRCEXT := cc
TARGET := bin/stdin-text-driver

rgb_libdir := matrix/lib
rgb_library := $(rgb_libdir)/librgbmatrix.a

src_dir := src
build_dir := build
sources := $(wildcard $(src_dir)/*.$(SRCEXT))
objects := $(patsubst $(src_dir)/%.$(SRCEXT),$(build_dir)/%.o,$(sources))

$(TARGET): $(objects) $(rgb_library)
	@echo " Linking..."
	$(CXX) $(LDFLAGS) -o $@ $^

$(build_dir)/%.o: $(src_dir)/%.$(SRCEXT)
	@echo " Compiling..."
	@mkdir -p $(build_dir)
	$(CXX) $(CXXFLAGS) -c -o $@ $<

$(rgb_library): librgbmatrix ;

.INTERMEDIATE: librgbmatrix
librgbmatrix:
	@echo " Building RGB matrix library..."
	$(MAKE) -C $(rgb_libdir)

.PHONY: clean mrproper
clean:
	@echo " Cleaning..."
	$(RM) -r $(build_dir) $(TARGET)

mrproper: clean
	@echo " Passing Mr. Proper..."
	$(MAKE) -C $(rgb_libdir) clean
