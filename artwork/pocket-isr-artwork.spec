Name:           pocket-isr-artwork
Version:        3
Release:        1%{?dist}
Summary:        Pocket ISR artwork
Group:          Applications/Multimedia
License:        CC-BY-SA
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch

%description
This package contains the Pocket ISR desktop background.

%prep
%setup -q

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc Attribution 'CC-BY-SA 3.0'
%{_datadir}/backgrounds/isr

%changelog
* Wed Oct 27 2010 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 3-1
- Update for F14

* Wed May 26 2010 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 2-1
- Update for F13

* Sun Jan 10 2010 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 1-1
- Initial package
