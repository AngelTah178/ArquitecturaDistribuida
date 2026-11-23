import pytest
from common.cluster_router import DynamicClusterRouter


def test_dynamic_cluster_routing_thresholds():
    router = DynamicClusterRouter()

    # Caso 1: 1 a 3 usuarios activos -> Cluster Mongo #1
    router.set_exact_active_users(1)
    assert router.get_target_cluster() == (1, "Cluster Mongo #1")

    router.set_exact_active_users(3)
    assert router.get_target_cluster() == (1, "Cluster Mongo #1")

    # Caso 2: 4 a 6 usuarios activos -> Cluster Mongo #2
    router.set_exact_active_users(4)
    assert router.get_target_cluster() == (2, "Cluster Mongo #2")

    router.set_exact_active_users(6)
    assert router.get_target_cluster() == (2, "Cluster Mongo #2")

    # Caso 3: 7 a 9 usuarios activos -> Cluster Mongo #3
    router.set_exact_active_users(7)
    assert router.get_target_cluster() == (3, "Cluster Mongo #3")

    router.set_exact_active_users(9)
    assert router.get_target_cluster() == (3, "Cluster Mongo #3")


def test_user_session_touch_and_remove():
    router = DynamicClusterRouter(session_ttl_seconds=10)
    router.touch_user("user_a", "Bot A")
    router.touch_user("user_b", "Bot B")

    assert router.get_active_users_count() == 2
    assert router.get_target_cluster() == (1, "Cluster Mongo #1")

    router.remove_user("user_a")
    assert router.get_active_users_count() == 1
    assert router.get_target_cluster() == (1, "Cluster Mongo #1")
