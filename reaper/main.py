"""
main.py prepares the session config and starts Reaper,
which executes its __startup.lua, which calls main.lua,
which calls the ReaScripts for the session, which control Reaper to produce audio.
main.py collects the session artifacts and checks them.
"""


def main():
    """
    main.py prepares the session config and starts Reaper,
    which executes its __startup.lua, which calls main.lua,
    which calls the ReaScripts for the session, which control Reaper to produce audio.
    main.py collects the session artifacts and checks them.
    """
    prepare_session_config()
    start_reaper()
    collect_session_artifacts()
    check_session_artifacts()


def prepare_session_config():
    """
    Prepares the session config file used by main.lua.
    """
    # add track to project
    # add Serum VST to track
    # set Serum VST parameters
    # add MIDI to track
    raise NotImplementedError("prepare_session_config not implemented")


def start_reaper():
    """
    Starts Reaper.
    """
    raise NotImplementedError("start_reaper not implemented")


def collect_session_artifacts():
    """
    Collects the session artifacts.
    """
    raise NotImplementedError("collect_session_artifacts not implemented")


def check_session_artifacts():
    """
    Checks the session artifacts.
    """
    raise NotImplementedError("check_session_artifacts not implemented")


if __name__ == "__main__":
    main()
