VERSION = 2
NAME = pocket-isr-artwork-$(VERSION)

BACKGROUND_DIR = $(DESTDIR)/usr/share/backgrounds/isr

all:

install:
	mkdir -p $(BACKGROUND_DIR)
	install -p -m644 -D standard.jpg $(BACKGROUND_DIR)

dist:
	mkdir -p $(NAME)
	cp -a COPYING Credits Makefile standard.jpg $(NAME)
	tar czf $(NAME).tar.gz $(NAME)
	rm -rf $(NAME)
