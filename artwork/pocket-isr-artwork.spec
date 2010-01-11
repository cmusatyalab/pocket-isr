Name:           pocket-isr-artwork
Version:        1
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
%doc COPYING Credits
%{_datadir}/backgrounds/isr

%changelog
* Sun Jan 10 2010 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 1-1
- Initial package
