%define gobuild(o:) %{expand:
  # https://bugzilla.redhat.com/show_bug.cgi?id=995136#c12
  %global _dwz_low_mem_die_limit 0
  %ifnarch ppc64
  go build -buildmode pie -compiler gc -tags="rpm_crashtraceback ${BUILDTAGS:-}" -ldflags "${LDFLAGS:-}%{?currentgoldflags} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n') -extldflags '%__global_ldflags %{?__golang_extldflags}' -compressdwarf=false" -a -v -x %{?**};
  %else
  go build                -compiler gc -tags="rpm_crashtraceback ${BUILDTAGS:-}" -ldflags "${LDFLAGS:-}%{?currentgoldflags} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n') -extldflags '%__global_ldflags %{?__golang_extldflags}' -compressdwarf=false" -a -v -x %{?**};
  %endif
}

# https://github.com/dnscrypt/dnscrypt-proxy
%global goipath         github.com/dnscrypt/dnscrypt-proxy
Version:                2.1.20
%global tag             2.1.20

%global common_description %{expand:
A flexible DNS proxy, with support for modern encrypted DNS protocols such as
DNSCrypt v2 and DNS-over-HTTP/2.

Features:

 - DNS traffic encryption and authentication. Supports DNS-over-HTTPS (DoH)
 and DNSCrypt.
 - DNSSEC compatible
 - DNS query monitoring, with separate log files for regular and suspicious
 queries
 - Pattern-based local blocking of DNS names and IP addresses
 - Time-based filtering, with a flexible weekly schedule
 - Transparent redirection of specific domains to specific resolvers
 - DNS caching, to reduce latency and improve privacy
 - Local IPv6 blocking to reduce latency on IPv4-only networks
 - Load balancing: pick a set of resolvers, dnscrypt-proxy will automatically
 measure and keep track of their speed, and balance the traffic across the
 fastest available ones.
 - Cloaking: like a HOSTS file on steroids, that can return preconfigured
 addresses for specific names, or resolve and return the IP address of other
 names. This can be used for local development as well as to enforce safe
 search results on Google, Yahoo and Bing.
 - Automatic background updates of resolvers lists
 - Can force outgoing connections to use TCP; useful with tunnels such as Tor.}

Name:           dnscrypt-proxy2
Release:        1%{?dist}
Summary:        Flexible DNS proxy, with support for encrypted DNS protocols

License:        ISC
URL:            https://github.com/dnscrypt/dnscrypt-proxy
Source0:        %{url}/archive/%{version}/dnscrypt-proxy-%{version}.tar.gz

# Largely inspired by Arch packaging
#Patch0:         dnscrypt-proxy-2.1.1-custom_config.patch

# e.g. el6 has ppc64 arch without gcc-go, so EA tag is required
ExclusiveArch:  %{?go_arches:%{go_arches}}%{!?go_arches:%{ix86} x86_64 aarch64 %{arm}}
# If go_compiler is not set to 1, there is no virtual provide. Use golang instead.
#BuildRequires:  %{?go_compiler:compiler(go-compiler)}%{!?go_compiler:golang}

%description
%{common_description}

%prep
%autosetup -p1 -n dnscrypt-proxy-%{version}

%build
curl -O -L https://go.dev/dl/go1.27.3.linux-amd64.tar.gz
mkdir -p %{buildroot}%/usr/local
tar -C %{buildroot}/usr/local -xzf go1.27.3.linux-amd64.tar.gz
export PATH=$PATH:%{buildroot}/usr/local/go/bin
export GO111MODULE=on
export GOFLAGS=-mod=vendor
ln -s $(pwd) vendor/github.com/jedisct1/dnscrypt-proxy
%gobuild -o _bin/dnscrypt-proxy %{goipath}/dnscrypt-proxy

%install
install -m 0755 -vd                          %{buildroot}%{_bindir}
install -m 0755 -vp _bin/dnscrypt-proxy      %{buildroot}%{_bindir}/
install -Dpm 0644 dnscrypt-proxy/example-dnscrypt-proxy.toml %{buildroot}%{_sysconfdir}/dnscrypt-proxy/dnscrypt-proxy.toml
install -Dpm 0644 dnscrypt-proxy/example-allowed-ips.txt %{buildroot}%{_sysconfdir}/dnscrypt-proxy/allowed-ips.txt
install -Dpm 0644 dnscrypt-proxy/example-allowed-names.txt  %{buildroot}%{_sysconfdir}/dnscrypt-proxy/allowed-names.txt
install -Dpm 0644 dnscrypt-proxy/example-blocked-ips.txt  %{buildroot}%{_sysconfdir}/dnscrypt-proxy/blocked-ips.txt
install -Dpm 0644 dnscrypt-proxy/example-blocked-names.txt  %{buildroot}%{_sysconfdir}/dnscrypt-proxy/blocked-names.txt
install -Dpm 0644 dnscrypt-proxy/example-captive-portals.txt  %{buildroot}%{_sysconfdir}/dnscrypt-proxy/captive-portals.txt
install -Dpm 0644 dnscrypt-proxy/example-cloaking-rules.txt  %{buildroot}%{_sysconfdir}/dnscrypt-proxy/cloaking-rules.txt
install -Dpm 0644 dnscrypt-proxy/example-forwarding-rules.txt  %{buildroot}%{_sysconfdir}/dnscrypt-proxy/forwarding-rules.txt

%post
if [ "$1" -le "1" ] ; then # First install
  dnscrypt-proxy -service install --config %{_sysconfdir}/dnscrypt-proxy/dnscrypt-proxy.toml
fi
if [ "$1" -ge "2" ] ; then
  # Remove in F36
  rm -rf %{_unitdir}/dnscrypt-proxy.service %{_unitdir}/dnscrypt-proxy.socket
fi

%preun
if [ "$1" -lt "1" ] ; then # Final removal
  dnscrypt-proxy -service uninstall
fi

%postun
if [ "$1" -ge "1" ] ; then # Upgrade
  dnscrypt-proxy -service install --config %{_sysconfdir}/dnscrypt-proxy/dnscrypt-proxy.toml
fi

%files
%license LICENSE
%doc README.md ChangeLog
%doc utils/generate-domains-blocklist/
%{_bindir}/dnscrypt-proxy
%dir %{_sysconfdir}/dnscrypt-proxy/
%config(noreplace) %{_sysconfdir}/dnscrypt-proxy/dnscrypt-proxy.toml
%config(noreplace) %{_sysconfdir}/dnscrypt-proxy/*.txt
%ghost %config(noreplace) %{_sysconfdir}/dnscrypt-proxy/blacklist.txt
%ghost %config(noreplace) %{_sysconfdir}/dnscrypt-proxy/whitelist.txt
%ghost %{_sysconfdir}/systemd/system/dnscrypt-proxy.service

%changelog
* Tue Nov 03 2026 defkev <defkev@gmail.com> - 2.1.20-1
- Update to 2.1.1

* Sat Oct 23 2021 Robert-André Mauchin <zebob.m@gmail.com> - 2.1.1-1
- Update to 2.1.1
- Close: rhbz#1969330

* Tue Mar 30 2021 Robert-André Mauchin <zebob.m@gmail.com> - 2.0.45-1
- Since version 2.0.45, some of the configuration files have been renamed.
Please merge your config to /etc/dnscrypt-proxy/dnscrypt-proxy.toml.rpmnew then
replace dnscrypt-proxy.toml with that file.
Read /usr/share/doc/dnscrypt-proxy/ChangeLog to know more about this change.
- generate-domains-blocklist is now provided in /usr/share/doc/dnscrypt-proxy/
- Fix: rhbz#1943749
- Update to 2.0.45
- Close: rhbz#1912171

* Mon Dec 28 2020 Robert-André Mauchin <zebob.m@gmail.com> - 2.0.44-4
- Reorder scriptlets
- Install service with link toward correct config file
- Force removal of previous service file

* Wed Dec 16 2020 Robert-André Mauchin <zebob.m@gmail.com> - 2.0.44-3
- Fallback to recommended installation

* Mon Dec 14 2020 Robert-André Mauchin <zebob.m@gmail.com> - 2.0.44-2
- Use an override to specify sockets

* Wed Jun 17 2020 Robert-André Mauchin <zebob.m@gmail.com> - 2.0.44-1
- Update to 2.0.44

* Mon Jan 20 2020 Robert-André Mauchin <zebob.m@gmail.com> - 2.0.39-1
- EPEL 7 build (#1792010)