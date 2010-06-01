Name:           pocket-isr-tools
Version:        1.2.1
Release:        1%{?dist}
Summary:        Tools for Pocket ISR live image

Group:          System Environment/Base
License:        GPLv2
URL:            http://isr.cmu.edu/
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  glib2-devel device-mapper-devel libblkid-devel
BuildRequires:  e2fsprogs-devel ntfsprogs-devel

Requires:       notify-python pygtk2
# For show_isr_storage
Requires:       PyYAML
# For pocket_isr_update.  -release is required for the GPG key.  gvfs is
# required for HTTP hyperlinking to work (RH #544119).
Requires:       gvfs livecd-tools pocket-isr-release pygpgme
Requires:       rb_libtorrent-python

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
%{_bindir}/pocket_isr_update
%{_bindir}/show_isr_storage
%{_sbindir}/gather_free_space
%{_sbindir}/remount_live_volume

%post
/sbin/chkconfig --add early-scratch-setup

%preun
/sbin/chkconfig --del early-scratch-setup

%changelog
* Tue Jun 01 2010 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 1.2.1-1
- show_isr_storage:
  - Fix window flickering at program startup on F13
- Pocket ISR Update:
  - Fix window flickering when starting update on F13

* Wed May 12 2010 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 1.2-1
- gather_free_space:
  - Add -r/--report option to produce machine-readable results report
  - Don't print invalid statistics if no extents are found
- early-scratch-setup:
  - Write transient storage report to /var/lib/transient-storage-info
  - Exclude all LiveCD-specific devices from gather_free_space run (cosmetic)
  - Create transient home partition with 0% reserved blocks
- show_isr_storage:
  - New application replacing check_isr_storage
  - Add details window showing the composition of transient storage
- Pocket ISR Update:
  - Eliminate dependency on nscd
- remount_live_volume:
  - Change owner of USB device root directory to liveuser on ext[234]
- Update package dependencies
- Other minor improvements

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
