import unittest

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from enlace_digital.interface.models import (
    Grupo,
    Neighborhood,
    Review,
    ReviewAnswer,
    School,
    SchoolGroup,
    SchoolGroupStats,
    Subgrupo,
    User,
)
from enlace_digital.interface.repositories import (
    NeighborhoodRepository,
    ReviewRepository,
    SchoolRepository,
    UserRepository,
)
from enlace_digital.settings.get_db import Base, configure_sqlite_connection


class RepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        event.listen(self.engine, "connect", configure_sqlite_connection)
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        self.neighborhoods = NeighborhoodRepository(self.session, Neighborhood)
        self.schools = SchoolRepository(
            self.session,
            School,
            group_model=SchoolGroup,
            stats_model=SchoolGroupStats,
        )
        self.reviews = ReviewRepository(
            self.session,
            Review,
            answer_model=ReviewAnswer,
            stats_model=SchoolGroupStats,
        )
        self.users = UserRepository(self.session, User)

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_neighborhood_and_school_upserts_are_idempotent(self) -> None:
        neighborhood = self.neighborhoods.get_or_create("Centro", "Recife")
        duplicate_neighborhood = self.neighborhoods.get_or_create("Centro", "Recife")
        self.assertEqual(neighborhood.id, duplicate_neighborhood.id)

        school = self.schools.upsert(
            name="Escola Árvore",
            neighborhood_id=neighborhood.id,
            address="Rua A",
            groups=[Grupo.MOBILIDADE, Grupo.VISUAL],
        )
        updated_school = self.schools.upsert(
            name="Escola Arvore",
            neighborhood_id=neighborhood.id,
            address="Rua B",
            groups=[Grupo.VISUAL],
        )

        self.assertEqual(school.id, updated_school.id)
        self.assertEqual(updated_school.name_normalized, "escola arvore")
        self.assertEqual(updated_school.address, "Rua B")
        profile = self.schools.get_profile(updated_school.id)
        self.assertIsNotNone(profile)
        assert profile is not None
        self.assertEqual(profile.groups, (Grupo.VISUAL,))

    def test_school_search_orders_by_matched_groups_without_duplicating_stats(self) -> None:
        neighborhood = self.neighborhoods.get_or_create("Boa Viagem", "Recife")
        complete = self.schools.upsert(
            name="Escola Completa",
            neighborhood_id=neighborhood.id,
            groups=[Grupo.MOBILIDADE, Grupo.VISUAL],
        )
        partial = self.schools.upsert(
            name="Escola Parcial",
            neighborhood_id=neighborhood.id,
            groups=[Grupo.MOBILIDADE],
        )
        self.session.add_all(
            [
                SchoolGroupStats(
                    school_id=complete.id,
                    group=Grupo.MOBILIDADE,
                    review_count=1,
                    score_sum=4,
                ),
                SchoolGroupStats(
                    school_id=complete.id,
                    group=Grupo.VISUAL,
                    review_count=1,
                    score_sum=2,
                ),
                SchoolGroupStats(
                    school_id=partial.id,
                    group=Grupo.MOBILIDADE,
                    review_count=1,
                    score_sum=5,
                ),
            ]
        )
        self.session.flush()

        results = self.schools.list_schools(
            neighborhood_id=neighborhood.id,
            groups=[Grupo.MOBILIDADE, Grupo.VISUAL],
        )

        self.assertEqual(
            [result.school.id for result in results], [complete.id, partial.id]
        )
        self.assertEqual([result.matched_group_count for result in results], [2, 1])
        self.assertEqual([result.average_score for result in results], [3.0, 5.0])

        all_schools = self.schools.list_schools(search="escola compléta")
        self.assertEqual([item.school.id for item in all_schools], [complete.id])

    def test_review_creation_updates_stats_and_public_list_hides_identity(self) -> None:
        neighborhood = self.neighborhoods.get_or_create("Várzea", "Recife")
        school = self.schools.upsert(
            name="Escola",
            neighborhood_id=neighborhood.id,
            groups=[Grupo.MOBILIDADE],
        )
        user = self.users.create("person@example.org", "strong-hash")
        registered_review = self.reviews.create(
            school_id=school.id,
            group=Grupo.MOBILIDADE,
            user_id=user.id,
            answers=[
                (Subgrupo.RAMPAS, 5),
                (Subgrupo.BANHEIRO_ACESSIVEL, 3),
            ],
        )
        anonymous_review = self.reviews.create(
            school_id=school.id,
            group=Grupo.MOBILIDADE,
            answers=[(Subgrupo.RAMPAS, 2)],
        )
        results = self.reviews.list_public(school.id, Grupo.MOBILIDADE)
        self.assertEqual(
            [review.id for review in results],
            [registered_review.id, anonymous_review.id],
        )
        self.assertTrue(results[0].from_registered_user)
        self.assertFalse(results[1].from_registered_user)
        self.assertEqual(results[0].score, 4)
        self.assertEqual(len(results[0].answers), 2)
        self.assertFalse(hasattr(results[0], "user_id"))
        self.assertFalse(hasattr(results[0], "email"))

        stats = self.session.scalar(
            select(SchoolGroupStats).where(
                SchoolGroupStats.school_id == school.id,
                SchoolGroupStats.group == Grupo.MOBILIDADE,
            ).execution_options(populate_existing=True)
        )
        self.assertIsNotNone(stats)
        assert stats is not None
        self.assertEqual(stats.review_count, 2)
        self.assertEqual(stats.score_sum, 6)
        profile = self.schools.get_profile(school.id)
        self.assertIsNotNone(profile)
        assert profile is not None
        refreshed_stats = profile.group_stats[0]
        self.assertEqual(refreshed_stats.review_count, 2)
        self.assertEqual(refreshed_stats.score_sum, 6)

    def test_review_rejects_answers_outside_group_or_scale(self) -> None:
        neighborhood = self.neighborhoods.get_or_create("Casa Forte", "Recife")
        school = self.schools.upsert(
            name="Escola",
            neighborhood_id=neighborhood.id,
        )

        with self.assertRaises(ValueError):
            self.reviews.create(
                school_id=school.id,
                group=Grupo.MOBILIDADE,
                answers=[(Subgrupo.PISO_TATIL, 3)],
            )
        with self.assertRaises(ValueError):
            self.reviews.create(
                school_id=school.id,
                group=Grupo.MOBILIDADE,
                answers=[(Subgrupo.RAMPAS, 6)],
            )
        with self.assertRaisesRegex(ValueError, "Duplicate answer"):
            self.reviews.create(
                school_id=school.id,
                group=Grupo.MOBILIDADE,
                answers=[
                    (Subgrupo.RAMPAS, 3),
                    (Subgrupo.RAMPAS, 4),
                ],
            )
        with self.assertRaises(ValueError):
            self.reviews.create(
                school_id=school.id,
                group=Grupo.MOBILIDADE,
                answers=[],
            )

        self.assertEqual(self.session.scalars(select(Review)).all(), [])

    def test_user_repository_looks_up_account_by_email(self) -> None:
        user = self.users.create("person@example.org", "hash")
        found_by_email = self.users.get_by_email(user.email)
        self.assertIsNotNone(found_by_email)
        assert found_by_email is not None
        self.assertEqual(found_by_email.id, user.id)
        self.assertIsNone(self.users.get_by_email("missing@example.org"))
        found_by_id = self.users.get_by_id(user.id)
        self.assertIsNotNone(found_by_id)
        assert found_by_id is not None
        self.assertEqual(found_by_id.id, user.id)


if __name__ == "__main__":
    unittest.main()
