#
# acinclude.m4 - extra autoconf macros
#
# Copyright (C) 2007-2008 Carnegie Mellon University
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of version 2 of the GNU General Public License as published
# by the Free Software Foundation.  A copy of the GNU General Public License
# should have been distributed along with this program in the file
# COPYING.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#

# FIND_LIBRARY([PRETTY_NAME], [LIBRARY_NAME], [LIBRARY_FUNCTION],
#              [HEADER_LIST], [PATH_LIST])
# The paths in PATH_LIST are searched to determine whether they contain the
# first header in HEADER_LIST.  If so, that path is added to the include and
# library paths.  Then the existence of all headers in HEADER_LIST, and of
# LIBRARY_FUNCTION within LIBRARY_NAME, is validated.  $FOUND_PATH is
# set to the name of the directory we've decided on.
# -----------------------------------------------------------------------------
AC_DEFUN([FIND_LIBRARY], [
	AC_MSG_CHECKING([for $1])
	for firsthdr in $4; do break; done
	found_lib=0
	for path in $5
	do
		if test -r $path/include/$firsthdr ; then
			found_lib=1
			CPPFLAGS="$CPPFLAGS -I${path}/include"
			LDFLAGS="$LDFLAGS -L${path}/lib"
			AC_MSG_RESULT([$path])
			break
		fi
	done
	
	if test $found_lib = 0 ; then
		AC_MSG_RESULT([not found])
		AC_MSG_ERROR([cannot find $1 in $5])
	fi
	
	# By default, AC_CHECK_LIB([foo], ...) will add "-lfoo" to the linker
	# flags for ALL programs and libraries, which is not what we want.
	# We put a no-op in the third argument to disable this behavior.
	AC_CHECK_HEADERS([$4],, AC_MSG_FAILURE([cannot find $1 headers]))
	AC_CHECK_LIB([$2], [$3], :, AC_MSG_FAILURE([cannot find $1 library]))
	FOUND_PATH=$path
])
