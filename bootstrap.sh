#!/usr/bin/env bash
# neon-shell bootstrap: a freshly installed CachyOS -> this whole desktop with all my apps, in one run.
#
#   curl -fsSL https://raw.githubusercontent.com/electrocrem/neon-shell/main/bootstrap.sh | bash
#   (or: git clone https://github.com/electrocrem/neon-shell ~/neon-shell && ~/neon-shell/bootstrap.sh)
#
#   --dry-run      only print what would happen (no sudo, nothing installed)
#   --no-aur       skip apps/aur.txt          --no-flatpak   skip apps/flatpak.txt
#   --no-desktop   apps only, do not run ./install.sh
#
# Steps: repo packages (packages.txt + apps/pacman.txt + what the hardware needs) -> AUR (apps/aur.txt, paru) -> Flatpak (apps/flatpak.txt)
# -> services (SDDM as the login screen, Bluetooth, firewall) and zsh as the shell -> ./install.sh --system (the desktop, login/boot screens).
# Hardware is detected: ASUS laptops get asusctl + ROG Control Center, AMD laptops ryzenadj, hybrid NVIDIA laptops the blind-login guard.
# Personal data is NOT copied. Every step is safe to run again; a package that fails is reported at the end and the rest goes on.
# Install CachyOS first with its normal installer (any desktop, or none): it sets up disks, kernel, GPU drivers and the boot loader.
set -uo pipefail

REPO_URL=https://github.com/electrocrem/neon-shell
DRY=0 AUR=1 FLATPAK=1 DESKTOP=1
for a in "$@"; do
    case $a in
        --dry-run) DRY=1 ;;
        --no-aur) AUR=0 ;;
        --no-flatpak) FLATPAK=0 ;;
        --no-desktop) DESKTOP=0 ;;
        -h | --help) sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown option: $a (see --help)" >&2; exit 2 ;;
    esac
done

if [[ -t 1 ]]; then C1=$'\e[38;2;46;211;215m' C2=$'\e[38;2;240;200;80m' C3=$'\e[38;2;240;80;80m' C0=$'\e[0m'; else C1= C2= C3= C0=; fi
say()  { printf '%s//%s %s\n' "$C1" "$C0" "$*"; }
warn() { printf '%s[warn]%s %s\n' "$C2" "$C0" "$*"; PROBLEMS+=("$*"); }
die()  { printf '%s[fail]%s %s\n' "$C3" "$C0" "$*" >&2; exit 1; }
run()  { if ((DRY)); then printf '   (dry) %s\n' "$*"; else "$@"; fi; }
PROBLEMS=()

[[ $EUID -ne 0 ]] || die "run as your normal user, not root (sudo is asked for once)"
command -v pacman >/dev/null || die "this is for CachyOS / Arch (pacman not found)"

# ------------------------------------------------------------------ started through curl | bash: fetch the repo, run the real copy
SELF=${BASH_SOURCE[0]:-}
if [[ -z $SELF || ! -f $(dirname "$SELF")/install.sh ]]; then
    DEST=$HOME/neon-shell
    command -v git >/dev/null || { say "installing git"; sudo pacman -S --needed --noconfirm git || die "cannot install git"; }
    if [[ -d $DEST/.git ]]; then git -C "$DEST" pull --ff-only || warn "could not update $DEST, using it as it is"
    else git clone "$REPO_URL" "$DEST" || die "cannot clone $REPO_URL"; fi
    exec bash "$DEST/bootstrap.sh" "$@" </dev/tty
fi
REPO=$(cd "$(dirname "$SELF")" && pwd)
LOG=$HOME/.local/share/gits-install/bootstrap-$(date +%Y%m%d-%H%M%S).log
if ((!DRY)); then mkdir -p "${LOG%/*}"; exec > >(tee -a "$LOG") 2>&1; fi

. /etc/os-release
[[ $ID == cachyos ]] || warn "not CachyOS ($PRETTY_NAME): packages that only CachyOS ships (paru, cachyos-zsh-config, vesktop-bin...) will be skipped"

# one password prompt for the whole run: keep the sudo timestamp fresh while the long steps (AUR builds) work
if ((!DRY)); then
    say "sudo is needed for packages and services"
    sudo -v || die "sudo failed"
    ( while kill -0 $$ 2>/dev/null; do sudo -n true 2>/dev/null; sleep 50; done ) &
    KEEP=$!
    trap 'kill $KEEP 2>/dev/null' EXIT
fi

list() { grep -vE '^\s*(#|$)' "$1" | awk '{print $1}'; }

# ------------------------------------------------------------------ hardware
vendor=$(cat /sys/class/dmi/id/sys_vendor 2>/dev/null)
chassis=$(cat /sys/class/dmi/id/chassis_type 2>/dev/null)
laptop=0; [[ $chassis =~ ^(8|9|10|11|14|30|31|32)$ ]] && laptop=1
gpus=$(lspci -nn 2>/dev/null | grep -Ei 'vga|3d|display')
nvidia=0; grep -qi '10de' <<<"$gpus" && nvidia=1
hybrid=0; ((nvidia)) && (( $(wc -l <<<"$gpus") > 1 )) && hybrid=1
amdcpu=0; grep -q AuthenticAMD /proc/cpuinfo && amdcpu=1
HW_PKGS=() HW_AUR=()
[[ $vendor == ASUSTeK* ]] && HW_PKGS+=(asusctl rog-control-center)
((nvidia)) && HW_PKGS+=(lib32-nvidia-utils)       # Steam / Proton; the driver itself comes from the CachyOS installer (chwd)
((amdcpu && laptop)) && HW_AUR+=(ryzenadj)
say "hardware: ${vendor:-unknown vendor}, $( ((laptop)) && echo laptop || echo desktop ), $( ((amdcpu)) && echo AMD || echo Intel/other ) CPU,$( ((nvidia)) && echo " NVIDIA GPU" )$( ((hybrid)) && echo " (hybrid)" )"
if ((nvidia)) && ! pacman -Qq nvidia-utils >/dev/null 2>&1; then
    warn "NVIDIA GPU but no nvidia-utils: run  sudo chwd -a  (CachyOS driver tool) and reboot, then run this again"
fi

# ------------------------------------------------------------------ 1. repo packages
say "updating the system and installing packages (packages.txt + apps/pacman.txt)"
run sudo pacman -Syu --noconfirm || warn "system update failed"
mapfile -t want < <( { list "$REPO/packages.txt"; list "$REPO/apps/pacman.txt"; printf '%s\n' "${HW_PKGS[@]}"; } | sort -u )
avail=$(pacman -Slq 2>/dev/null | sort -u)
mapfile -t ok < <(comm -12 <(printf '%s\n' "${want[@]}") <(printf '%s\n' "$avail"))
mapfile -t gone < <(comm -23 <(printf '%s\n' "${want[@]}") <(printf '%s\n' "$avail"))
((${#gone[@]})) && warn "not in the repos, skipped: ${gone[*]}"
if ((${#ok[@]})); then
    if ! run sudo pacman -S --needed --noconfirm "${ok[@]}"; then
        # one bad package (conflict, a file clash) fails the whole transaction: retry one by one to install everything else
        warn "pacman failed for the batch, retrying package by package"
        for p in "${ok[@]}"; do pacman -Qq "$p" >/dev/null 2>&1 || sudo pacman -S --needed --noconfirm "$p" >/dev/null 2>&1 || warn "pacman: $p failed"; done
    fi
fi

# ------------------------------------------------------------------ 2. AUR
if ((AUR)); then
    mapfile -t aur < <( { list "$REPO/apps/aur.txt"; printf '%s\n' "${HW_AUR[@]}"; } | sort -u )
    if ! command -v paru >/dev/null && ((!DRY)); then
        warn "paru not installed, AUR apps skipped: ${aur[*]}"
    else
        say "AUR: ${aur[*]}"
        for p in "${aur[@]}"; do
            pacman -Qq "$p" >/dev/null 2>&1 && continue
            run paru -S --needed --noconfirm --skipreview "$p" || warn "AUR: $p failed to build"
        done
    fi
fi

# ------------------------------------------------------------------ 3. Flatpak
if ((FLATPAK)); then
    mapfile -t fp < <(list "$REPO/apps/flatpak.txt")
    say "Flatpak: ${#fp[@]} apps from Flathub"
    run sudo flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo || warn "cannot add Flathub"
    for app in "${fp[@]}"; do
        flatpak info "$app" >/dev/null 2>&1 && continue
        run sudo flatpak install -y --noninteractive flathub "$app" || warn "flatpak: $app failed"
    done
fi

# ------------------------------------------------------------------ 4. services, groups, shell
say "services"
for dm in plasma-login-manager plasmalogin cosmic-greeter gdm lightdm ly greetd; do
    systemctl is-enabled "$dm.service" >/dev/null 2>&1 && { run sudo systemctl disable "$dm.service"; say "  login screen $dm -> sddm"; }
done
for unit in sddm bluetooth ufw; do
    systemctl list-unit-files "$unit.service" >/dev/null 2>&1 && ! systemctl is-enabled "$unit.service" >/dev/null 2>&1 &&
        { run sudo systemctl enable "$unit.service" || warn "cannot enable $unit"; }
done
command -v ufw >/dev/null && ! sudo -n ufw status 2>/dev/null | grep -q 'Status: active' && run sudo ufw --force enable >/dev/null
getent group wireshark >/dev/null && ! id -nG | grep -qw wireshark && run sudo usermod -aG wireshark "$USER"
if [[ $(getent passwd "$USER" | cut -d: -f7) != */zsh ]] && command -v zsh >/dev/null; then
    say "zsh as the login shell"
    run sudo chsh -s "$(command -v zsh)" "$USER" || warn "chsh failed"
fi

# ------------------------------------------------------------------ 5. the desktop
if ((DESKTOP)); then
    say "installing the desktop (./install.sh --system)"
    args=(--system); ((hybrid)) && args+=(--login-guards)
    ((DRY)) && args+=(--dry-run)
    bash "$REPO/install.sh" "${args[@]}" || warn "install.sh reported a problem (see above)"
fi

# ------------------------------------------------------------------ summary
echo
if ((${#PROBLEMS[@]})); then
    say "done, with ${#PROBLEMS[@]} problem(s):"
    printf '   - %s\n' "${PROBLEMS[@]}"
else
    say "done, no problems"
fi
((DRY)) || say "log: $LOG"
say "reboot, pick the Hyprland session at the login screen. Theme: gits-theme select (Super+I -> Appearance)."
