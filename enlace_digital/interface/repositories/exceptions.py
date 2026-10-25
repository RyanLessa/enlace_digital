class SchoolNotFound(LookupError):
    def __init__(self, school_id: int) -> None:
        self.school_id = school_id
        super().__init__(f"Escola com ID {school_id} não encontrada.")


class ReviewNotFound(LookupError):
    def __init__(self, school_id: int, user_id: int) -> None:
        self.school_id = school_id
        self.user_id = user_id
        super().__init__(
            f"Revisão da escola {school_id} pelo usuário {user_id} não encontrada."
        )


class SchoolScoreNotFound(LookupError):
    def __init__(self, school_id: int, group: object) -> None:
        self.school_id = school_id
        self.group = group
        super().__init__(
            f"Pontuação da escola {school_id} para o grupo {group} não encontrada."
        )
