"""Tests for the singleton helper utility."""

from src.helpers.singleton import Singleton, SingletonMeta


def test_singleton_meta_returns_same_instance_and_preserves_first_arguments():
    SingletonMeta._instances.clear()

    class SampleSingleton(metaclass=SingletonMeta):
        def __init__(self, value: int = 0, *, label: str = "") -> None:
            self.value = value
            self.label = label

    first = SampleSingleton(5, label="first")
    second = SampleSingleton(99, label="second")

    assert first is second
    assert first.value == 5
    assert first.label == "first"
    assert SingletonMeta._instances[SampleSingleton] is first


def test_singleton_base_class_behaves_like_singleton_across_reinstantiation():
    SingletonMeta._instances.clear()

    class Config(Singleton):
        def __init__(self, *, mode: str = "default") -> None:
            self.mode = mode
            self.created = True

    first = Config(mode="prod")
    second = Config(mode="dev")

    assert first is second
    assert first.mode == "prod"
    assert second.mode == "prod"
    assert first.created is True
