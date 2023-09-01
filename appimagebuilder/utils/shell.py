import logging
import shutil


class CommandNotFoundError(RuntimeError):
    pass


def require_executables(executables: [str]):
    """
    Iterates through all items in <executables> searching for their paths
    :return: map with the command name and its path
    """
    return {dep: require_executable(dep) for dep in executables}


def require_executable(tool):
    if tool_path := shutil.which(tool):
        return tool_path
    else:
        raise CommandNotFoundError("Could not find '{exe}' on $PATH.".format(exe=tool))


def assert_successful_result(proc):
    if proc.returncode:
        logging.error(f'"{proc.args}" execution failed')
        if proc.stderr:
            for line in proc.stderr.decode().splitlines():
                logging.error(line)

        raise RuntimeError(
            f'"{proc.args}" execution failed with code {proc.returncode}'
        )
