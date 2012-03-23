Name:		pocket-isr-release
Version:	2
Release:	1
Summary:	Pocket ISR repository configuration

Group:		System Environment/Base
License:	GPLv2
URL:		http://isr.cmu.edu/
Source0:	pocket-isr.repo
Source1:	RPM-GPG-KEY-pocket-isr
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:	noarch

%description
This package contains the Pocket ISR repository configuration for the Yum
package manager, as well as the GPG public key which signs the Pocket ISR
packages.

%prep

%build

%install
rm -rf %{buildroot}
install -Dpm 644 %{SOURCE0} %{buildroot}%{_sysconfdir}/yum.repos.d/pocket-isr.repo
install -Dpm 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-pocket-isr

%clean 
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/yum.repos.d/pocket-isr.repo
%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-pocket-isr

%changelog
* Thu Mar 22 2012 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 2-1
- Update GPG key expiration

* Sun Jan 10 2010 Benjamin Gilbert <bgilbert@cs.cmu.edu> - 1-1
- Initial release using OpenISR release-signing key
