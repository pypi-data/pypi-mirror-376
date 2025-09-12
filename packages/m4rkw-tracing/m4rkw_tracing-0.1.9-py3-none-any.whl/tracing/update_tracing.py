#!/usr/bin/env python3

import datetime
import os
import pwd
import sys

import yaml

from tracing import Tracing


class UpdateTracing:

    def __init__(self) -> None:
        self.hostname: str = os.popen("hostname").read().rstrip().split(".")[0]


    def main(self) -> None:
        lm = Tracing(f"{self.hostname}_update_tracing")

        try:
            config = yaml.safe_load(open("/etc/tracing.yaml"))

            self.homedir = pwd.getpwuid(os.getuid()).pw_dir
            statefile = f"{self.homedir}/.tracing.yaml"

            if os.path.isfile(statefile):
                state = yaml.safe_load(open(statefile))
            else:
                state = {}

            username = pwd.getpwuid(os.getuid()).pw_name

            if username not in config['users']:
                lm.success()
                return

            updated = False

            for venv in config['users'][username]:
                new_version = self.update(venv['path'])

                if 'apps' not in venv:
                    continue

                for app in venv['apps']:
                    if app not in state or state[app] != new_version:
                        if self.refresh_app(app, venv['apps'][app]):
                            self.log(f"refreshed {app} to version {new_version}")
                            state[app] = new_version
                            updated = True

            if updated:
                with open(statefile + '.new', "w") as f:
                    yaml.dump(state, f)
                os.rename(statefile + '.new', statefile)

            lm.success()

        except Exception as e:
            lm.failure()
            self.log(f"exception: {e}")

            if sys.stdin.isatty():
                raise e


    def log(self, message: str) -> None:
        if not os.path.exists(f"{self.homedir}/.log"):
            os.mkdir(f"{self.homedir}/.log")

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"[{timestamp}] {message}\n"

        with open(f"{self.homedir}/.log/update_tracing.log", "a+") as f:
            f.write(message)

        if sys.stdout.isatty():
            print(message, end='')


    def update(self, path: str) -> str:
        lpwd = os.getcwd()

        os.chdir(path)

        self.set_path()

        current_version = os.popen("uv pip list |grep m4rkw-tracing").read().rstrip().split()[1]

        os.system("uv pip install --upgrade m4rkw-tracing -n 1>/dev/null 2>/dev/null")

        new_version = os.popen("uv pip list |grep m4rkw-tracing").read().rstrip().split()[1]

        if current_version != new_version:
            self.log(f"updated venv {path} from {current_version} to {new_version}")

        os.chdir(lpwd)

        return new_version


    def set_path(self) -> None:
        path = os.environ['PATH']

        path = f"{path}:/opt/local/bin:{self.homedir}/.local/bin"

        os.environ['PATH'] = path


    def refresh_app(self, app: str, steps: list[str]) -> bool:
        for step in steps:
            self.log(f"refreshing app {app} with step: {step}")
            if os.system(step) != 0:
                self.log(f"failed to refresh app {app} with step: {step}")
                return False

        return True


if __name__ == "__main__":
    updater = UpdateTracing()
    updater.main()

def main() -> None:
    updater = UpdateTracing()
    updater.main()
