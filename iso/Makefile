include ../vars.mk

OUTDIR = ../output
CACHE = cache
-include ../local.mk

DESC = Pocket-ISR-$(VERSION)
KICKSTART = pocket-isr.ks

ifeq ($(LOCALREPO),1)
REPO := file://$(abspath $(OUTDIR))/$(ARCH)/
else
REPO := http://isr.cmu.edu/software/pocket-isr/repo/!!FVER!!/$$basearch/
endif

.PHONY: image
image: need_root
	@# Regenerate the kickstart file every time, since REPO might be
	@# set differently by the caller
	sed -e 's|!!REPO!!|$(REPO)|g' -e 's/!!FVER!!/$(FVER)/g' \
		-e 's/!!VERSION!!/$(VERSION)/g' \
		-e 's:!!TOP_SRCDIR!!:$(abspath ..):g' \
		$(KICKSTART).in > $(KICKSTART)
	mkdir -p $(OUTDIR)
	ln -sf $(OUTDIR)/$(DESC).iso $(DESC).iso
	setarch $(ARCH) livecd-creator -c $(KICKSTART) -f $(DESC) \
		--cache=$(CACHE)
	rm -f $(DESC).iso

.PHONY: need_root
need_root:
	@[ `id -u` = 0 ] || ( echo "You must be root." ; exit 1 )

.PHONY: clean
clean: need_root
	rm -f $(OUTDIR)/$(DESC).iso $(KICKSTART)

.PHONY: mrproper
mrproper: clean
	rm -rf $(CACHE)

.PHONY: distribute
distribute:
	$(ISO_DIST) $(OUTDIR)/$(DESC).iso

.PHONY: mount
mount: need_root
	mkdir mount_iso mount_squash mount_ext3
	mount -o loop $(OUTDIR)/$(DESC).iso mount_iso
	mount -o loop mount_iso/LiveOS/squashfs.img mount_squash
	mount -o loop mount_squash/LiveOS/ext3fs.img mount_ext3

.PHONY: unmount
unmount: need_root
	umount mount_ext3
	umount mount_squash
	umount mount_iso
	rmdir mount_iso mount_squash mount_ext3
