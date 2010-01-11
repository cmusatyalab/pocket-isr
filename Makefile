OUTDIR = output

ARCH := $(shell rpm --eval %{_target_cpu})

ifdef LOCALREPO
REPO := file://$(abspath $(OUTDIR))/$(ARCH)/
endif

ifdef KEEPDIR
rmtmpdir = echo "Build directory for spec file $(1) retained at $(2)"
else
rmtmpdir = rm -rf $(2)
endif

# $1 = sources
# $2 = specfile
buildpackage = @tmp=`mktemp -dt pocket-isr-rpm-XXXXXXXX` && \
	mkdir -p $$tmp/BUILD $$tmp/RPMS $$tmp/SOURCES $$tmp/SPECS \
		$$tmp/SRPMS && \
	cp $(1) $$tmp/SOURCES/ && \
	rpmbuild -ba --define "_topdir $$tmp" $(2) && \
	mkdir -p $(OUTDIR)/SRPMS $(OUTDIR)/$(ARCH)/debug && \
	mv $$tmp/SRPMS/*.rpm $(OUTDIR)/SRPMS && \
	(mv $$tmp/RPMS/*/*debuginfo*.rpm $(OUTDIR)/$(ARCH)/debug \
		2>/dev/null ||:) && \
	mv $$tmp/RPMS/*/*.rpm $(OUTDIR)/$(ARCH) && \
	$(call rmtmpdir,$(2),$$tmp)

.PHONY: all
# Does not include "iso", since that needs root permissions to build
all: artwork tools repo createrepo

.PHONY: artwork
artwork:
	rm -f artwork/*.tar.gz
	$(MAKE) -C artwork dist
	$(call buildpackage,artwork/*.tar.gz,artwork/*.spec)

.PHONY: tools
tools:
	rm -f tools/*.tar.gz
	cd tools && autoreconf -fi
	cd tools && ./configure
	$(MAKE) -C tools distcheck
	$(call buildpackage,tools/*.tar.gz,tools/*.spec)

.PHONY: repo
repo:
	$(call buildpackage,repo/*.repo repo/RPM-GPG-KEY-*,repo/*.spec)

.PHONY: createrepo
createrepo:
	createrepo -d $(OUTDIR)/SRPMS
	createrepo -d $(OUTDIR)/$(ARCH)
	createrepo -d $(OUTDIR)/$(ARCH)/debug

.PHONY: iso
iso:
	make -C iso image $(if $(REPO),REPO=$(REPO),)

.PHONY: clean
clean:
	rm -rf $(OUTDIR)
