AM_CPPFLAGS  = -W -Wall -Wstrict-prototypes
AM_CPPFLAGS += -D_GNU_SOURCE -D_FILE_OFFSET_BITS=64

initdir = $(sysconfdir)/rc.d/init.d

dist_bin_SCRIPTS = pocket_isr_update show_isr_storage
dist_sbin_SCRIPTS = remount_live_volume
sbin_PROGRAMS = gather_free_space
dist_init_SCRIPTS = early-scratch-setup

gather_free_space_CFLAGS  = $(glib_CFLAGS) $(blkid_CFLAGS) $(devmapper_CFLAGS)
gather_free_space_CFLAGS += $(ext2fs_CFLAGS)
gather_free_space_LDFLAGS  = $(glib_LIBS) $(blkid_LIBS) $(devmapper_LIBS)
gather_free_space_LDFLAGS += $(ext2fs_LIBS) -lntfs
