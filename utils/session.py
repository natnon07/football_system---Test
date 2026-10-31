class CurrentSession:
    _user_id = None
    _username = None
    _role = None

    @classmethod
    def login(cls, user_id, username, role):
        cls._user_id = user_id
        cls._username = username
        cls._role = role

    @classmethod
    def get_user_id(cls):
        return cls._user_id

    @classmethod
    def get_username(cls):
        return cls._username

    @classmethod
    def get_role(cls):
        return cls._role

    @classmethod
    def is_authenticated(cls):
        return cls._user_id is not None

    @classmethod
    def logout(cls):
        cls._user_id = None
        cls._username = None
        cls._role = None