#
# Copyright (C) 2006-2009 Sun Microsystems, Inc.
# Copyright (C) 2009-2010 Carnegie Mellon University
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, in version 2 as it comes in the "COPYING" file
# of the VirtualBox OSE distribution. VirtualBox OSE is distributed in the
# hope that it will be useful, but WITHOUT ANY WARRANTY of any kind.
#

# find-debuginfo.sh chokes on *.r0 without this
%undefine _missing_build_ids_terminate_build

Summary: 	VirtualBox OSE
Name: 		virtualbox-ose-3.0
Version: 	3.0.12
Release: 	1%{?dist}
Group: 		Applications/System
License:	GPLv2 and (GPLv2 or CDDL)

BuildRequires:	gcc-c++ dev86 iasl openssl-devel libxml2-devel libxslt-devel
BuildRequires:	libXcursor-devel qt-devel libIDL-devel SDL-devel
BuildRequires:	alsa-lib-devel pulseaudio-libs-devel hal-devel libcap-devel
BuildRequires:	python-devel gsoap-devel libXmu-devel mesa-libGL-devel
BuildRequires:	mesa-libGLU-devel libcurl-devel
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

Requires:	gcc binutils make dkms chkconfig /usr/sbin/groupadd
Conflicts:	VirtualBox

URL:		http://www.virtualbox.org/
Source0:	http://download.virtualbox.org/virtualbox/%{version}/VirtualBox-%{version}-OSE.tar.bz2
Source1:	virtualbox-ose-LocalConfig.kmk
Source2:	virtualbox-ose-VBox.sh

%description
VirtualBox is a powerful PC virtualization solution allowing you to run a
wide range of PC operating systems on your Linux system. This includes
Windows, Linux, FreeBSD, DOS, OpenBSD and others. VirtualBox comes with
a broad feature set and excellent performance, making it the premier
virtualization software solution on the market.

%prep
%setup -q -n VirtualBox-%{version}_OSE

%build
cp %{SOURCE1} LocalConfig.kmk
# Web service disabled, since it has build problems
./configure --ose
source $(pwd)/env.sh
kmk --no-print-directory \
	PATH_OUT=$(pwd)/out \
	VBOX_DO_STRIP= \
	VBOX_DO_STRIP_MODULES= \
	VBOX_WITH_MULTIVERSION_PYTHON= \
	VBOX_WITHOUT_ADDITIONS=1 \
	VBOX_WITH_REGISTRATION_REQUEST= \
	VBOX_WITH_UPDATE_REQUEST= \
	all

%install
rm -rf %{buildroot}
install -d %{buildroot}/etc/rc.d/init.d
install -d %{buildroot}/etc/vbox
install -d %{buildroot}/usr/bin
install -d %{buildroot}/usr/lib/virtualbox
install -d %{buildroot}/usr/share/applications
install -d %{buildroot}/usr/share/virtualbox
install -d %{buildroot}/usr/share/pixmaps
install -d %{buildroot}/usr/src

cd out/bin
mv virtualbox.desktop %{buildroot}/usr/share/applications
mv VBox.png %{buildroot}/usr/share/pixmaps
mv *.gc %{buildroot}/usr/lib/virtualbox
mv *.r0 %{buildroot}/usr/lib/virtualbox
mv *.rel %{buildroot}/usr/lib/virtualbox || true
mv VBoxNetDHCP %{buildroot}/usr/lib/virtualbox
mv VBoxNetAdpCtl %{buildroot}/usr/lib/virtualbox
mv VBoxXPCOMIPCD %{buildroot}/usr/lib/virtualbox
mv components %{buildroot}/usr/lib/virtualbox
rm -f VBoxBFE.so
mv *.so %{buildroot}/usr/lib/virtualbox
mv *.so.4 %{buildroot}/usr/lib/virtualbox || true
mv VBoxTestOGL %{buildroot}/usr/lib/virtualbox
mv nls %{buildroot}/usr/share/virtualbox
mv src  %{buildroot}/usr/share/virtualbox
mv VBoxSysInfo.sh %{buildroot}/usr/share/virtualbox

cd sdk/installer
VBOX_INSTALL_PATH=/usr/lib/virtualbox \
	python ./vboxapisetup.py install --root %{buildroot}
cd ../..
mv vboxshell.py %{buildroot}/usr/lib/virtualbox
xpcom_path=%{buildroot}/usr/lib/virtualbox/sdk/bindings/xpcom
mkdir -p $xpcom_path
mv sdk/bindings/xpcom/python $xpcom_path

rm VBox.sh
cp %{SOURCE2} %{buildroot}/usr/bin/VBox
for i in VBoxManage VBoxSVC VBoxSDL VirtualBox VBoxHeadless; do
	mv $i %{buildroot}/usr/lib/virtualbox
done
mv VBoxTunctl %{buildroot}/usr/bin
for i in VirtualBox VBoxManage VBoxSDL VBoxHeadless ; do
	ln -s VBox %{buildroot}/usr/bin/$i
done

# --ose disables dkms setup for some reason, so we have to do it ourselves
inbase=../../src/VBox/HostDrivers
outbase=%{buildroot}/usr/share/virtualbox/src
cp $inbase/Support/linux/dkms.conf $outbase/vboxdrv/
cp $inbase/VBoxNetAdp/linux/dkms.conf $outbase/vboxnetadp/
cp $inbase/VBoxNetFlt/linux/dkms.conf $outbase/vboxnetflt/
for d in vboxdrv vboxnetflt vboxnetadp ; do
	cp $inbase/linux/do_Module.symvers $outbase/$d
	ln -s ../share/virtualbox/src/$d %{buildroot}/usr/src/$d-%{version}
	sed -ie 's/_VERSION_/%{version}/' $outbase/$d/dkms.conf
done

sed -e 's|%NOLSB%||g' -e 's|%DEBIAN%||g' -e 's|%PACKAGE%|virtualbox|g' \
	../../src/VBox/Installer/linux/vboxdrv.sh.in > \
	%{buildroot}/etc/rc.d/init.d/vboxdrv

%clean
rm -rf %{buildroot} out AutoConfig.kmk env.sh

%files
%defattr(-,root,root,-)
%dir /etc/vbox
%attr(755,root,root) /etc/rc.d/init.d/vboxdrv
/usr/bin/VBox
/usr/bin/VBoxHeadless
/usr/bin/VBoxManage
/usr/bin/VBoxSDL
/usr/bin/VBoxTunctl
/usr/bin/VirtualBox
/usr/lib/python*/site-packages/vboxapi*
# We have to list the contents of /usr/lib/virtualbox explicitly, since
# we need to override attributes on some files and we can't list files twice.
%attr(4511,root,root) /usr/lib/virtualbox/VirtualBox
%attr(4511,root,root) /usr/lib/virtualbox/VBoxHeadless
%attr(4511,root,root) /usr/lib/virtualbox/VBoxSDL
%attr(4511,root,root) /usr/lib/virtualbox/VBoxNetDHCP
%attr(4511,root,root) /usr/lib/virtualbox/VBoxNetAdpCtl
/usr/lib/virtualbox/vboxshell.py*
/usr/lib/virtualbox/VBoxManage
/usr/lib/virtualbox/VBoxSVC
/usr/lib/virtualbox/VBoxTestOGL
/usr/lib/virtualbox/VBoxXPCOMIPCD
/usr/lib/virtualbox/*.gc
/usr/lib/virtualbox/*.r0
/usr/lib/virtualbox/*.so
/usr/lib/virtualbox/components
/usr/lib/virtualbox/sdk
/usr/share/virtualbox
/usr/share/applications/virtualbox.desktop
/usr/share/pixmaps/VBox.png
# Symlinks
/usr/src/vboxdrv-%{version}
/usr/src/vboxnetadp-%{version}
/usr/src/vboxnetflt-%{version}
%doc COPYING COPYING.CDDL

%pre
# Check for active VMs
if pidof VBoxSVC > /dev/null 2>&1; then
	cat << EOF
A copy of VirtualBox is currently running.  Please close it and try again.
Please note that it can take up to ten seconds for VirtualBox (in particular
the VBoxSVC daemon) to finish running.
EOF
	exit 1
fi

%post
if [ "$1" = 1 ] ; then
	cat > /etc/udev/rules.d/60-vboxdrv.rules <<EOF
KERNEL=="vboxdrv", NAME="vboxdrv", OWNER="root", GROUP="root", MODE="0600"
EOF
fi
/usr/sbin/groupadd --force --system vboxusers
/sbin/chkconfig --add vboxdrv
for m in vboxdrv vboxnetflt vboxnetadp; do
	/usr/sbin/dkms add -q -m $m -v %{version} --rpm_safe_upgrade
	/usr/sbin/dkms build -m $m -v %{version} ||:
	/usr/sbin/dkms install -m $m -v %{version} ||:
done
/etc/rc.d/init.d/vboxdrv start ||:

%preun
if [ "$1" = 0 ] ; then
	/etc/rc.d/init.d/vboxdrv stop
	/sbin/chkconfig --del vboxdrv
	rm -f /etc/udev/rules.d/60-vboxdrv.rules
fi
for m in vboxdrv vboxnetflt vboxnetadp; do
	/usr/sbin/dkms remove -q -m $m -v %{version} --all --rpm_safe_upgrade
done

%changelog
* Tue Jan 12 2010 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 3.0.12-1
- Initial package
