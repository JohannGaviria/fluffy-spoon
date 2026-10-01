import pytest
from faker import Faker

from tests.helpers import unreachable_services


@pytest.fixture
def faker() -> Faker:
    return Faker()


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Skip infrastructure-dependent tests when the services are unreachable.

    The `db` marker means "this test needs a real PostgreSQL and/or Redis". Those
    services are only reachable from inside the Docker network, where the hosts
    in `DATABASE_URL` and `REDIS_URL` resolve to the compose service names. When
    the suite runs directly on the host (`poetry run pytest`), that same URL
    points at a name that does not resolve, so every `db` test would fail with a
    `socket.gaierror` that says nothing about the code under test.

    Instead of failing, those tests are skipped with an actionable reason. To
    actually exercise them, run the suite through Docker with
    `make test-integration`, `make test-e2e` or `make test`, which puts the
    runner inside the network where the hosts resolve.

    Args:
        config: The pytest configuration object.
        items: The collected test items, modified in place.
    """
    unavailable = unreachable_services()
    if not unavailable:
        return

    reason = (
        f"{' and '.join(unavailable)} not reachable at the configured URL. "
        "Run these tests through Docker (e.g. `make test-integration`) or point "
        "the corresponding URL at a reachable instance."
    )

    skip_marker = pytest.mark.skip(reason=reason)

    for item in items:
        if "db" in item.keywords:
            item.add_marker(skip_marker)
