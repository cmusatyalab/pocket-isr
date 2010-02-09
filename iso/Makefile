include ../vars.mk

REPO = http://isr.cmu.edu/software/pocket-isr/repo/!!FVER!!/$$basearch/
CACHE = cache

DESC = Pocket-ISR-$(VERSION)
KICKSTART = pocket-isr.ks

.PHONY: image
image: need_root
	@# Regenerate the kickstart file every time, since REPO might be
	@# set differently by the caller
	sed -e 's|!!REPO!!|$(REPO)|g' -e 's/!!FVER!!/$(FVER)/g' \
		$(KICKSTART).in > $(KICKSTART)
	setarch $(ARCH) livecd-creator -c $(KICKSTART) -f $(DESC) \
		--cache=$(CACHE)

.PHONY: need_root
need_root:
	@[ `id -u` = 0 ] || ( echo "You must be root." ; exit 1 )

.PHONY: clean
clean: need_root
	rm -f *.iso $(KICKSTART)

.PHONY: mrproper
mrproper: clean
	rm -rf $(CACHE)

.PHONY: mount
mount: need_root
	mkdir mount_iso mount_squash mount_ext3
	mount -o loop $(DESC).iso mount_iso
	mount -o loop mount_iso/LiveOS/squashfs.img mount_squash
	mount -o loop mount_squash/LiveOS/ext3fs.img mount_ext3

.PHONY: unmount
unmount: need_root
	umount mount_ext3
	umount mount_squash
	umount mount_iso
	rmdir mount_iso mount_squash mount_ext3
