from dulwich import index
from dulwich.client import HttpGitClient
from dulwich.repo import Repo
from func_timeout import FunctionTimedOut, func_timeout

from pathlib import Path


REMOTE_URL = "https://github.com/nahco314/agc77-minigames"


def _fetch():
    if Path("./assets/").exists():
        local_repo = Repo("./assets/")
    else:
        local_repo = Repo.init("./assets/", mkdir=True)
    remote_repo = HttpGitClient(REMOTE_URL)
    remote_refs = remote_repo.fetch(REMOTE_URL, local_repo)
    local_repo[b"HEAD"] = remote_refs[b"refs/heads/main"]

    index_file = local_repo.index_path()
    tree = local_repo[b"HEAD"].tree
    index.build_index_from_tree(local_repo.path, index_file, local_repo.object_store, tree)


def fetch():
    try:
        if Path("./assets/").exists():
            func_timeout(5, _fetch)
        else:
            func_timeout(60, _fetch)

        print("fetch done!")

    except FunctionTimedOut as e:
        print("fetch timeout!!!")
        print(e)

    except Exception as e:
        print("fetch failed!!!")
        print(e)
