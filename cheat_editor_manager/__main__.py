from __future__ import annotations

import os

from .bootstrap import configure_tcl_environment


configure_tcl_environment()

from .app import App


def main() -> None:
    app = App()
    if os.environ.get("CHEAT_EDITOR_MANAGER_SMOKE_EXIT") == "1":
        app.root.update_idletasks()
        app.root.update()
        app.root.destroy()
        return
    app.run()


if __name__ == "__main__":
    main()
