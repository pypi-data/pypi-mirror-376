from typing import Callable, Any, Type, Union
import inspect


class DIContainer:
    def __init__(self):
        self._registrations: dict[Type, Callable] = {}
        self._registrations_by_name: dict[str, Callable] = {}

        self._singletons: dict[Type, Callable] = {}
        self._singletons_by_name: dict[str, Callable] = {}

        self._singleton_instances: dict[Type, Any] = {}
        self._singleton_instances_by_name: dict[str, Any] = {}

    def register(self, cls: Type, factory: Callable = None, name: str | None = None):
        """Register dependency."""
        self._registrations[cls] = factory or cls
        if name:
            self._registrations_by_name[name] = factory or cls

    def register_singleton(self, cls: Type, factory: Callable = None, name: str | None = None):
        """Register singleton."""
        if cls in self._singletons or cls in self._singleton_instances:
            raise ValueError(f'{factory} is already registered as singleton.')
        self._singletons[cls] = factory or cls
        if name:
            self._singletons_by_name[name] = factory or cls

    def register_instance(self, cls: Type, instance: Any, name: str | None = None):
        """Register singleton instance."""
        if cls in self._singletons or cls in self._singleton_instances:
            raise ValueError(f'{cls} is already registered as singleton.')
        self._singleton_instances[cls] = instance
        self._singletons[cls] = cls
        if name:
            self._singleton_instances_by_name[name] = instance
            self._singletons_by_name[name] = cls

    def resolve(self, key: Union[Type, str], *,
                depends: dict[Type, Any] | None = None,
                options: dict[str, Any] | None = None) -> Any:
        """
        Resolve dependency.
        Args:
            - depends - dependency provided in depends it has priority to use
            - options - options for cls
        """
        return self._resolve_internal(key, depends or {}, options or {}, set())

    def _resolve_internal(self, key: Union[Type, str],
                          depends: dict[Type, Any],
                          options: dict[str, Any],
                          stack: set) -> Any:
        if isinstance(key, str):
            if key in self._singleton_instances_by_name:
                return self._singleton_instances_by_name[key]
        else:
            if key in self._singleton_instances:
                return self._singleton_instances[key]

        if key in depends:
            return depends[key]

        if isinstance(key, str):
            factory = self._registrations_by_name.get(key) or self._singletons_by_name.get(key)
        else:
            factory = self._registrations.get(key) or self._singletons.get(key)
        if not factory:
            raise ValueError(f"Dependency {key} is not registered")

        if key in stack:
            raise ValueError(f"Cyclic dependency detected for {key}")
        stack.add(key)

        sig = inspect.signature(factory)
        resolved_args = {}

        for name, param in sig.parameters.items():
            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                raise ValueError(
                    f"Missing type annotation for parameter '{name}' in {key}")

            if name in options:
                resolved_args[name] = options[name]
            elif param_type in depends:
                resolved_args[name] = depends[param_type]
            elif param_type in self._singleton_instances:
                resolved_args[name] = self._singleton_instances[param_type]
            elif param_type in self._registrations or param_type in self._singletons:
                resolved_args[name] = self._resolve_internal(param_type, depends, {}, stack)
            elif param.default != inspect.Parameter.empty:
                resolved_args[name] = param.default
            else:
                raise ValueError(
                    f"Cannot resolve parameter '{name}' for {key}")

        stack.remove(key)
        instance = factory(**resolved_args)

        if isinstance(key, str):
            if key in self._singletons_by_name:
                self._singleton_instances_by_name[key] = instance
        else:
            if key in self._singletons:
                self._singleton_instances[key] = instance

        return instance


if __name__ == "__main__":
    # ===== Тесты DIContainer =====

    class MailClient:
        def __init__(self):
            self.host = "smtp.example.com"

    class Service:
        def __init__(self, client: MailClient):
            self.client = client

    c = DIContainer()

    c.register_singleton(MailClient, name="MailClient")
    c.register(Service)

    # --- singleton по типу ---
    mc1 = c.resolve(MailClient)
    mc2 = c.resolve(MailClient)
    assert mc1 is mc2, "Singleton по типу должен возвращать один и тот же экземпляр"

    # --- singleton по имени ---
    mc3 = c.resolve("MailClient")
    assert mc3 is mc1, "Singleton по имени должен совпадать с экземпляром по типу"

    # --- resolve зависимость с вложенными зависимостями ---
    s1 = c.resolve(Service)
    assert isinstance(s1.client, MailClient), "Service должен получить MailClient"

    # --- транзиент возвращает новый экземпляр ---
    s2 = c.resolve(Service)
    assert s1 is not s2, "Transient должен возвращать новый объект"

    print("✅ Все тесты успешно пройдены!")
