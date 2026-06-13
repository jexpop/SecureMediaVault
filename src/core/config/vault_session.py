class VaultSession:

    _password = None
    _metadata_key = None

    @classmethod
    def set_password(
        cls,
        password: str
    ):

        cls._password = password

    @classmethod
    def get_password(cls):

        return cls._password

    @classmethod
    def set_metadata_key(
        cls,
        key: bytes
    ):
        """
        Stores the derived AES-256 key used to
        encrypt/decrypt metadata (filenames, tags...).
        """

        cls._metadata_key = key

    @classmethod
    def get_metadata_key(cls) -> bytes:

        return cls._metadata_key

    @classmethod
    def clear(cls):
        """
        Clears the in-memory session (password and
        metadata key). Call on lock/logout.
        """

        cls._password = None
        cls._metadata_key = None