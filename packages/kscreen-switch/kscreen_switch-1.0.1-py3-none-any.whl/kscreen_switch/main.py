#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path

KSCREEN_SWITCH_DIR = Path("~").expanduser() / ".config" / "kscreen-switch"
PROFILES_DIR = KSCREEN_SWITCH_DIR / "profiles"
KSCREEN_DOCTOR_CMD = "kscreen-doctor"


def print_sys_info():
    print("System info:")
    print(run_command(['plasmashell', '--version'], check_output=True).decode(sys.getfilesystemencoding()).strip())


def ensure_profiles_dir():
    PROFILES_DIR.mkdir(exist_ok=True, parents=True)


def run_command(cmd, check_output=False):
    try:
        if check_output:
            return subprocess.check_output(cmd, stderr=subprocess.PIPE).strip()
        else:
            subprocess.run(cmd, check=True, text=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Command execution error '{' '.join(cmd)}':")
        print(f"Exit code: {e.returncode}")
        print(f"Standard error output: {e.stderr.strip()}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Command ‘{cmd[0]}’ not found. Make sure it is in your PATH.")
        sys.exit(1)


def get_profile_path(profile_name):
    if not profile_name:
        return None
    return PROFILES_DIR / f"{profile_name}.json"


class Profile:
    def __init__(self, profile_name, verbose=False, dry_run=False):
        if not profile_name:
            raise ValueError("A profile name is required for this operation.")

        self.profile_name = profile_name
        self.verbose = verbose
        self.dry_run = dry_run

    def save_profile(self):
        ensure_profiles_dir()
        profile_path = get_profile_path(self.profile_name)

        if profile_path.exists():
            print(f"Profile {self.profile_name} already exists.")
            exit(1)

        print(f"Saving the current configuration to '{self.profile_name}'...")
        output = run_command([KSCREEN_DOCTOR_CMD, "-j"], check_output=True)
        self._verbose(output)
        if not self.dry_run:
            with open(profile_path, "w") as f:
                f.write(output.decode(sys.getfilesystemencoding()))
            print(f"Profile successfully saved '{self.profile_name}'.")

    def _verbose(self, message):
        if self.verbose:
            print('VERB: ', message)

    def load_profile(self):
        # TODO: Implement other properties https://github.com/deepin-community/libkscreen/blob/4628110e1954a498b353060160385ace9a526c4a/src/doctor/kscreen-doctor.zsh#L21
        profile_path = get_profile_path(self.profile_name)
        if not profile_path.exists():
            print(f"Error: Profile ‘{self.profile_name}’ does not exist.")
            sys.exit(1)

        print(f"Loading configuration from profile '{self.profile_name}'...")
        profile_raw = profile_path.read_text()
        profile_json = json.loads(profile_raw)
        prof = []
        for output_profile in profile_json["outputs"]:
            name = output_profile["name"]
            position = f"{output_profile['pos']['x']},{output_profile['pos']['y']}"
            priority = f"{output_profile['priority']}"
            replicationSource = f"{output_profile['replicationSource']}"
            ROTATION_MAP = (
                'none', 'normal', 'left', 'right', 'inverted', 'flipped', 'flipped90', 'flipped180', 'flipped270'
            )
            rotation = ROTATION_MAP[output_profile['rotation']]
            scale = f"{output_profile['scale']}"
            modes = dict([(m['id'], m['name']) for m in output_profile['modes']])
            # print('A:', modes)
            mode = modes[output_profile['currentModeId']]

            p = f"output.{name}"
            # is enabled
            if output_profile['enabled']:
                prof.append(f"{p}.enable")
            else:
                prof.append(f"{p}.disable")
            prof.append(f"{p}.position.{position}")
            prof.append(f"{p}.priority.{priority}")
            # prof.append(f"{p}.replicationSource.{replicationSource}")
            prof.append(f"{p}.rotation.{rotation}")
            prof.append(f"{p}.scale.{scale}")
            prof.append(f"{p}.mode.{mode}")
        cmd = f"{KSCREEN_DOCTOR_CMD} {' '.join(prof)}"
        self._verbose(cmd)
        if not self.dry_run:
            run_command([KSCREEN_DOCTOR_CMD] + prof, check_output=True)
            print(f"Profile loaded successfully '{self.profile_name}'.")

    @staticmethod
    def list_profiles():
        ensure_profiles_dir()
        profiles = [f.name.replace(".json", "") for f in PROFILES_DIR.glob('*') if
                    f.is_file() and f.name.split('.')[-1] == 'json']
        if not profiles:
            print("No profiles saved.")
        else:
            print("Available profiles:")
            for profile in sorted(profiles):
                print(f"- {profile}")

    def delete_profile(self):
        profile_path = get_profile_path(self.profile_name)
        if not profile_path.exists():
            print(f"Error: Profile ‘{self.profile_name}’ does not exist.")
            sys.exit(1)

        if self.dry_run:
            print(f"DRY RUN: Profile '{self.profile_name}' would be deleted.")
            return

        try:
            prompt = f"Are you sure you want to permanently delete profile '{self.profile_name}'? [y/N]: "
            confirmation = input(prompt)
        except KeyboardInterrupt:
            print("\nDeletion cancelled by user.")
            sys.exit(130)

        if confirmation.lower() == 'y':
            print(f"Deleting profile '{self.profile_name}'...")
            os.remove(profile_path)
            print(f"Profile successfully deleted '{self.profile_name}'.")
        else:
            print("Deletion cancelled.")


def main():
    parser = argparse.ArgumentParser(
        prog='kscreen-switch',
        description="Managing monitor configuration profiles using kscreen-doctor.",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "-l", "--load",
        metavar="PROFILE_NAME",
        help="Loads and applies the monitor configuration from the specified profile."
    )
    group.add_argument(
        "-s", "--save",
        metavar="PROFILE_NAME",
        help="Saves the current monitor configuration to the specified profile."
    )
    group.add_argument(
        "-L", "--list",
        action="store_true",
        help="Displays a list of all saved profiles."
    )
    group.add_argument(
        "-d", "--delete",
        metavar="PROFILE_NAME",
        help="Removes the specified monitor configuration profile."
    )

    group2 = parser.add_argument_group()
    group2.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Detailed information about the application's activities."
    )
    group2.add_argument(
        "-D", "--dry-run",
        action="store_true",
        help="Launch the application without modifying the drive or monitors."
    )
    group2.add_argument(
        "-h", "--help",
        action="store_true",
        help="Launch the application without modifying the drive or monitors."
    )
    args = parser.parse_args()

    if args.help:
        parser.print_help()
        if args.verbose:
            print('\n\n')
            print_sys_info()
    elif args.save:
        Profile(profile_name=args.save, verbose=args.verbose, dry_run=args.dry_run).save_profile()
    elif args.load:
        Profile(profile_name=args.load, verbose=args.verbose, dry_run=args.dry_run).load_profile()
    elif args.list:
        Profile.list_profiles()
    elif args.delete:
        Profile(profile_name=args.delete, verbose=args.verbose, dry_run=args.dry_run).delete_profile()


if __name__ == "__main__":
    main()
