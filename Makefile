OUTDIR = output

ARCH := $(shell rpm --eval %{_target_cpu})

ifdef LOCALREPO
REPO := file://$(abspath $(OUTDIR))/$(ARCH)/
endif

# $1 = specfile
# $2 = tmpdir
ifdef KEEPDIR
rmtmpdir = echo "Build directory for spec file $(1) retained at $(2)"
else
rmtmpdir = rm -rf $(2)
endif

# $1 = specfile
# $2 = source number (omit for all)
getsources = $(shell awk '/Name:/ {name = $$2} \
	/Version:/ {ver = $$2} \
	/Source$(if $(2),$(2),[0-9]+):/ { \
		gsub("%{name}", name); \
		gsub("%{version}", ver); \
		print $$2 \
	}' $(1))

# $1 = specfile
buildpackage = @tmp=`mktemp -dt pocket-isr-rpm-XXXXXXXX` && \
	mkdir -p $$tmp/BUILD $$tmp/RPMS $$tmp/SOURCES $$tmp/SPECS \
		$$tmp/SRPMS && \
	cp $(addprefix $(dir $(1)),$(notdir $(call getsources,$(1)))) \
		$$tmp/SOURCES/ && \
	rpmbuild -ba --define "_topdir $$tmp" $(1) && \
	mkdir -p $(OUTDIR)/SRPMS $(OUTDIR)/$(ARCH)/debug && \
	mv $$tmp/SRPMS/*.rpm $(OUTDIR)/SRPMS && \
	(mv $$tmp/RPMS/*/*debuginfo*.rpm $(OUTDIR)/$(ARCH)/debug \
		2>/dev/null ||:) && \
	mv $$tmp/RPMS/*/*.rpm $(OUTDIR)/$(ARCH) && \
	$(call rmtmpdir,$(1),$$tmp)

.PHONY: all
# Does not include "iso", since that needs root permissions to build
all: artwork tools repo virtualbox createrepo

.PHONY: artwork
artwork:
	rm -f artwork/*.tar.gz
	$(MAKE) -C artwork dist
	$(call buildpackage,artwork/*.spec)

.PHONY: tools
tools:
	rm -f tools/*.tar.gz
	cd tools && autoreconf -fi
	cd tools && ./configure
	$(MAKE) -C tools distcheck
	$(call buildpackage,tools/*.spec)

.PHONY: repo
repo:
	$(call buildpackage,repo/*.spec)

.PHONY: virtualbox
virtualbox: VBOXURL := $(call getsources,virtualbox/*.spec,0)
virtualbox: VBOXSRC := virtualbox/$(notdir $(VBOXURL))
virtualbox:
	[ -f $(VBOXSRC) ] || wget -O $(VBOXSRC) $(VBOXURL)
	$(call buildpackage,virtualbox/*.spec)

.PHONY: createrepo
createrepo:
	createrepo -qd $(OUTDIR)/SRPMS
	createrepo -qd $(OUTDIR)/$(ARCH) -x 'debug/*'
	createrepo -qd $(OUTDIR)/$(ARCH)/debug

.PHONY: iso
iso:
	make -C iso image $(if $(REPO),REPO=$(REPO),)

.PHONY: clean
clean:
	rm -rf $(OUTDIR)

.PHONY: mrproper
mrproper: clean
	rm -f virtualbox/*.tar.bz2
