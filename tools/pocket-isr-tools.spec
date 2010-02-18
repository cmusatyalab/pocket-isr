Name:           pocket-isr-tools
Version:        1.0.2
Release:        1%{?dist}
Summary:        Tools for Pocket ISR live image

Group:          System Environment/Base
License:        GPLv2
URL:            http://isr.cmu.edu/
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  glib2-devel device-mapper-devel libblkid-devel
BuildRequires:  e2fsprogs-devel ntfsprogs-devel

Requires:       libnotify

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
%{_sbindir}/gather_free_space
%{_sbindir}/remount_live_volume

%post
/sbin/chkconfig --add early-scratch-setup

%preun
/sbin/chkconfig --del early-scratch-setup

%changelog
* Wed Jan 20 2010 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 1.0.2-1
- Add license block to early-scratch-setup script

* Wed Jan 13 2010 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 1.0.1-1
- Add check_isr_storage script

* Sun Jan 10 2010 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 1.0-1
- Initial package
