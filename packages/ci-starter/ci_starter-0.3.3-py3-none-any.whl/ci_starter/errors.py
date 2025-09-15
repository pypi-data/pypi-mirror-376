class CiStarterError(Exception):
    pass


class RemoteNotFoundError(CiStarterError):
    def __str__(self):
        return "could not find any remote in the repository"
