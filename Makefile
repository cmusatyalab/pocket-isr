include vars.mk

OUTDIR = output
-include local.mk

# $1 = specfile
# Returns all sources and patches
getsources = $(shell awk '/Name:/ {name = $$2} \
	/Version:/ {ver = $$2} \
	/(Source|Patch)[0-9]+:/ { \
		gsub("%{name}", name); \
		gsub("%{version}", ver); \
		print $$2 \
	}' $(1))

# $1 = specfile
buildpackage = @sources=`mktemp -dt pocket-isr-sources-XXXXXXXX` && \
	binaries=`mktemp -dt pocket-isr-binaries-XXXXXXXX` && \
	cp $(addprefix $(dir $(1)),$(notdir $(call getsources,$(1)))) \
		$$sources && \
	mock --buildsrpm -r "fedora-$(FVER)-$(ARCH)" -v --spec $(1) \
		--sources $$sources --resultdir $$binaries && \
	rm -r $$sources && \
	mock $$binaries/*.src.rpm -r "fedora-$(FVER)-$(ARCH)" -v \
		--resultdir $$binaries && \
	mkdir -p $(OUTDIR)/SRPMS $(OUTDIR)/$(ARCH)/debug && \
	mv $$binaries/*.src.rpm $(OUTDIR)/SRPMS && \
	(mv $$binaries/*debuginfo*.rpm $(OUTDIR)/$(ARCH)/debug \
		2>/dev/null ||:) && \
	mv $$binaries/*.rpm $(OUTDIR)/$(ARCH) && \
	rm -r $$binaries

.PHONY: all
# Does not include "iso", since that needs root permissions to build
all: artwork tools repo createrepo

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

.PHONY: createrepo
createrepo:
	createrepo -qd $(OUTDIR)/SRPMS
	createrepo -qd $(OUTDIR)/$(ARCH) -x 'debug/*'
	createrepo -qd $(OUTDIR)/$(ARCH)/debug

.PHONY: iso
iso:
	make -C iso image OUTDIR=$(abspath $(OUTDIR))

.PHONY: clean
clean:
	rm -rf $(OUTDIR)

.PHONY: distribute-packages
distribute-packages:
	$(PACKAGE_DIST) $(FVER) $(OUTDIR)

.PHONY: distribute-iso
distribute-iso:
	make -C iso distribute OUTDIR=$(abspath $(OUTDIR))
