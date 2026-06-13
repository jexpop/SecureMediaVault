class VaultSession:

    _password = None

    @classmethod
    def set_password(
        cls,
        password: str
    ):

        cls._password = password

    @classmethod
    def get_password(cls):

        return cls._password