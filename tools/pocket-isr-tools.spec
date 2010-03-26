Name:           pocket-isr-tools
Version:        1.1.2
Release:        1%{?dist}
Summary:        Tools for Pocket ISR live image

Group:          System Environment/Base
License:        GPLv2
URL:            http://isr.cmu.edu/
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  glib2-devel device-mapper-devel libblkid-devel
BuildRequires:  e2fsprogs-devel ntfsprogs-devel

# For check_isr_storage
Requires:       libnotify
# For pocket_isr_update.  -release is required for the GPG key.  gvfs is
# required for HTTP hyperlinking to work (RH #544119).
Requires:       notify-python pygtk2 gvfs livecd-tools pocket-isr-release
Requires:       pygpgme rb_libtorrent-python

%description
Tools for the Pocket ISR live image, including a utility to collect free
disk space into a device-mapper volume and an initscript to create transient
/home and swap partitions on free space during live image boot.

%prep
%setup -q

%build
%configure --enable-silent-rules
make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc COPYING
%{_initddir}/early-scratch-setup
%{_bindir}/check_isr_storage
%{_bindir}/pocket_isr_update
%{_sbindir}/gather_free_space
%{_sbindir}/remount_live_volume

%post
/sbin/chkconfig --add early-scratch-setup

%preun
/sbin/chkconfig --del early-scratch-setup

%changelog
* Fri Mar 26 2010 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 1.1.2-1
- gather_free_space: Reject extents < 4 MB by default to reduce seek overhead
- early-scratch-setup: Add min_extent_size kernel command-line parameter

* Wed Mar 24 2010 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 1.1.1-1
- Display 1024-based units as KB/MB/GB rather than KiB/MiB/GiB
- gather_free_space:
  - Use largest 10^5 extents rather than rejecting extents < 4 MB
  - Log additional statistics
  - Add -d/--dump option for statistical analysis
  - Fix compiler warnings on 64 bit
- Pocket ISR Update:
  - Don't be confused by captive portals
  - Refuse to downgrade Pocket ISR
- Other minor improvements

* Fri Feb 19 2010 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 1.1-1
- Add Pocket ISR Update application
- Add remount_live_volume script to mount /mnt/live with proper permissions
- Add -q option to check_isr_storage

* Wed Jan 20 2010 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 1.0.2-1
- Add license block to early-scratch-setup script

* Wed Jan 13 2010 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 1.0.1-1
- Add check_isr_storage script

* Sun Jan 10 2010 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 1.0-1
- Initial package
