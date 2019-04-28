CXXFLAGS=-Wall -O3 -g -Wextra -Wno-unused-parameter

RGB_LIB_DISTRIBUTION=matrix
RGB_INCDIR=$(RGB_LIB_DISTRIBUTION)/include
RGB_LIBDIR=$(RGB_LIB_DISTRIBUTION)/lib
RGB_LIBRARY_NAME=rgbmatrix
RGB_LIBRARY=$(RGB_LIBDIR)/lib$(RGB_LIBRARY_NAME).a
LDFLAGS+=-L$(RGB_LIBDIR) -l$(RGB_LIBRARY_NAME) -lrt -lm -lpthread

stdin-text-driver: stdin-text-driver.o $(RGB_LIBRARY)
	$(CXX) -o $@ $< $(LDFLAGS)

stdin-text-driver.o: stdin-text-driver.cc
	$(CXX) -c -o $@ $< $(CXXFLAGS) -I$(RGB_INCDIR)

$(RGB_LIBRARY): FORCE
	$(MAKE) -C $(RGB_LIBDIR)

.PHONY: clean mrproper
clean:
	$(RM) -f stdin-text-driver.o stdin-text-driver

mrproper: clean
	$(MAKE) -C $(RGB_LIBDIR) clean

.PHONY: FORCE
FORCE:
