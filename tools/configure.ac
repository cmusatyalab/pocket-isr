# Process this file with autoconf to produce a configure script.

AC_PREREQ([2.63])
AC_INIT([pocket-isr-tools], [1.2.1], [isr@cs.cmu.edu])
AC_CONFIG_AUX_DIR([build-aux])
AM_INIT_AUTOMAKE([foreign silent-rules 1.11])
AC_COPYRIGHT([Copyright (C) 2009 Carnegie Mellon University])
AC_CONFIG_SRCDIR([src/gather_free_space.c])
AC_CONFIG_HEADERS([config.h])
AM_SILENT_RULES

# Checks for programs.
AC_PROG_CC

# Checks for libraries.
PKG_CHECK_MODULES([glib], [glib-2.0])
PKG_CHECK_MODULES([blkid], [blkid])
PKG_CHECK_MODULES([devmapper], [devmapper])
PKG_CHECK_MODULES([ext2fs], [ext2fs])
# Needed for NTFS headers to parse correctly
AC_CHECK_HEADERS([stdarg.h])
FIND_LIBRARY([libntfs], [ntfs], [ntfs_mount], [ntfs/volume.h],
			[/usr/local /usr])

AC_CONFIG_FILES([Makefile src/Makefile])
AC_OUTPUT
