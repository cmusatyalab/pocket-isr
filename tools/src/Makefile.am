AM_CPPFLAGS  = -W -Wall -Wstrict-prototypes
AM_CPPFLAGS += -D_GNU_SOURCE -D_FILE_OFFSET_BITS=64

sbin_PROGRAMS = gather_free_space

gather_free_space_CFLAGS  = $(glib_CFLAGS) $(blkid_CFLAGS) $(devmapper_CFLAGS)
gather_free_space_CFLAGS += $(ext2fs_CFLAGS)
gather_free_space_LDFLAGS  = $(glib_LIBS) $(blkid_LIBS) $(devmapper_LIBS)
gather_free_space_LDFLAGS += $(ext2fs_LIBS) -lntfs
