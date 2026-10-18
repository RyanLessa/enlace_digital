class SchoolNotFound(LookupError):
    def __init__(self, school_id: int) -> None:
        self.school_id = school_id
        super().__init__(f"School {school_id} was not found or is inactive.")


class ReviewNotFound(LookupError):
    def __init__(self, school_id: int, user_id: int) -> None:
        self.school_id = school_id
        self.user_id = user_id
        super().__init__(
            f"Review for school {school_id} and user {user_id} was not found."
        )


class SchoolScoreNotFound(LookupError):
    def __init__(self, school_id: int, group: object) -> None:
        self.school_id = school_id
        self.group = group
        super().__init__(
            f"Score wallet for school {school_id} and group {group} was not found."
        )
