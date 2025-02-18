
import argparse
import os
import time
import sys

from fedml.cli.comm_utils.sys_utils import cleanup_all_fedml_server_api_processes,\
    cleanup_all_fedml_server_learning_processes,cleanup_all_fedml_server_login_processes, get_python_program, \
    daemon_ota_upgrade
from fedml.cli.server_deployment.server_constants import ServerConstants


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--type", "-t", help="Login or logout to MLOps platform")
    parser.add_argument("--user", "-u", type=str,
                        help='account id at MLOps platform')
    parser.add_argument("--version", "-v", type=str, default="release")
    parser.add_argument("--local_server", "-ls", type=str, default="127.0.0.1")
    parser.add_argument("--role", "-r", type=str, default="local")
    parser.add_argument("--runner_cmd", "-rc", type=str, default="{}")
    parser.add_argument("--device_id", "-id", type=str, default="0")
    parser.add_argument("--os_name", "-os", type=str, default="")
    args = parser.parse_args()
    args.user = args.user

    pip_source_dir = os.path.dirname(__file__)
    login_cmd = os.path.join(pip_source_dir, "server_login.py")

    while True:
        try:
            ServerConstants.cleanup_run_process()
            cleanup_all_fedml_server_api_processes()
            cleanup_all_fedml_server_learning_processes()
            cleanup_all_fedml_server_login_processes("server_login.py", clean_process_group=False)
        except Exception as e:
            pass

        daemon_ota_upgrade(args)

        login_pid = ServerConstants.exec_console_with_shell_script_list(
            [
                get_python_program(),
                "-W",
                "ignore",
                login_cmd,
                "-t",
                "login",
                "-u",
                str(args.user),
                "-v",
                args.version,
                "-ls",
                args.local_server,
                "-r",
                args.role,
                "-rc",
                args.runner_cmd,
                "-id",
                args.device_id,
                "-os",
                args.os_name
            ]
        )
        ret_code, exec_out, exec_err = ServerConstants.get_console_sys_out_pipe_err_results(login_pid)
        time.sleep(3)

        if args.role == ServerConstants.login_role_list[ServerConstants.LOGIN_MODE_CLOUD_SERVER_INDEX]:
            break


