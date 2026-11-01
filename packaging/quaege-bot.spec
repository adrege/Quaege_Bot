Name:           quaege-bot
Version:        1.0.0
Release:        1%{?dist}
Summary:        Quaege administration tools
License:        MIT
BuildArch:      x86_64
Requires:       libX11

%description
Desktop application for automating Quaege bookkeeping and balance-update emails.

%prep

%build

%install
install -d %{buildroot}/opt/quaege-bot
cp -a %{_sourcedir}/dist/Quaege_Bot/. %{buildroot}/opt/quaege-bot/
install -Dm755 %{_sourcedir}/packaging/quaege-bot-launcher.sh \
    %{buildroot}/usr/bin/quaege-bot
install -Dm644 %{_sourcedir}/packaging/quaege-bot.desktop \
    %{buildroot}/usr/share/applications/quaege-bot.desktop
install -Dm644 %{_sourcedir}/Adrege_logo.png \
    %{buildroot}/usr/share/icons/hicolor/256x256/apps/quaege-bot.png

%files
/opt/quaege-bot
/usr/bin/quaege-bot
/usr/share/applications/quaege-bot.desktop
/usr/share/icons/hicolor/256x256/apps/quaege-bot.png

%changelog
* Sun Nov 01 2026 Quaege Bot contributors - 1.0.0-1
- Initial Fedora package
