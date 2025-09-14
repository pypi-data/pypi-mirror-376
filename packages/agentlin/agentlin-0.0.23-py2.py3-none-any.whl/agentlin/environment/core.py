from typing import Optional, Type
import importlib
from importlib import util as import_util
import inspect

from loguru import logger

from agentlin.environment.interface import IEnvironment


def _format_default(param: inspect.Parameter) -> str:
    if param.default is inspect._empty:  # type: ignore[attr-defined]
        return f"{param.name}=<required>"
    dv = param.default
    if isinstance(dv, str):
        return f"{param.name}='{dv}'"
    return f"{param.name}={dv}"


def _resolve_module_and_class(env_path: str) -> tuple[str, Optional[str]]:
    """
    Resolve module path and optional class name from env_path.

    Supported forms:
    - "qa_env" -> module: qa_env (if importable) or agentlin.environment.qa_env (fallback)
    - "qa-env" -> module: agentlin.environment.qa_env
    - "agentlin.environment.qa_env" -> module: agentlin.environment.qa_env
    - "agentlin.environment.qa_env:QAEnv" -> module + class
    - "qa_env:QAEnv" -> module (prefixed) + class
    - "qa_env.QAEnv" (discouraged) will be treated as module path if it looks like a fully-qualified path;
      prefer colon to disambiguate.
    """
    module_part = env_path
    class_part: Optional[str] = None

    if ":" in env_path:
        module_part, class_part = env_path.split(":", 1)

    # normalize hyphens to underscores for module import
    module_part = module_part.replace("-", "_")

    # If it's not a fully qualified path, try unprefixed first, then fallback to agentlin.environment
    if not module_part.startswith("agentlin."):
        # Prefer unprefixed if it is importable on current sys.path
        try:
            if import_util.find_spec(module_part) is not None:
                return module_part, class_part
        except Exception:
            pass
        fallbacks = [
            f"agentlin.environment.{module_part}",
            f"agentlin.environments.{module_part}",
            # f"environments.{module_part}",
        ]
        for fallback in fallbacks:
            # If fallback exists, use it; otherwise still return fallback and let caller raise a clear error
            try:
                if import_util.find_spec(fallback) is not None:
                    return fallback, class_part
            except Exception:
                continue
        return fallback, class_part

    return module_part, class_part


def _pick_env_class(module, class_name: Optional[str]) -> Type[IEnvironment]:
    candidates = []
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, IEnvironment) and obj is not IEnvironment:
            candidates.append(obj)

    if class_name:
        for c in candidates:
            if c.__name__ == class_name:
                return c
        raise AttributeError(f"Class '{class_name}' not found in module '{module.__name__}' or not a subclass of IEnvironment")

    if not candidates:
        raise AttributeError(f"No IEnvironment subclass found in module '{module.__name__}'. Provide a load_environment() function or specify a class via '<module>:<ClassName>'.")

    # Heuristics: exact 'Env' > name ending with 'Env' > first candidate
    for c in candidates:
        if c.__name__ == "Env":
            return c
    for c in candidates:
        if c.__name__.endswith("Env"):
            return c
    return candidates[0]


def load_environment(env_path: str, **env_args) -> IEnvironment:
    """
    动态加载环境模块并实例化环境对象。

    优先策略：
    1) 若模块定义了 load_environment(**kwargs)，则调用并返回结果。
    2) 否则在模块中查找 IEnvironment 的子类并尝试用 **kwargs 实例化（可通过 '<module>:<Class>' 指定类）。

    参数示例：
    - "qa_env" 或 "qa-env"
    - "agentlin.environment.qa_env"
    - "qa_env:QAEnv" 或 "agentlin.environment.qa_env:QAEnv"
    """
    logger.info(f"Loading environment {env_path}")
    module_name, class_name = _resolve_module_and_class(env_path)
    logger.info(f"Environment module name {module_name}")
    if class_name:
        logger.info(f"Requested environment class {class_name}")

    if env_args:
        logger.info(f"Environment args provided ({len(env_args)} total): {env_args}")
    else:
        logger.info("No environment args provided, using defaults")

    try:
        module = importlib.import_module(module_name)

        # Path A: explicit module-level load_environment
        if hasattr(module, "load_environment") and inspect.isfunction(module.load_environment):  # type: ignore[attr-defined]
            env_load_func = module.load_environment  # type: ignore[attr-defined]
            try:
                sig = inspect.signature(env_load_func)
                defaults_info = [_format_default(param) for param in sig.parameters.values()]
                if defaults_info:
                    logger.debug("Environment defaults: " + ", ".join(defaults_info))

                if env_args:
                    provided_params = set(env_args.keys())
                    all_params = set(sig.parameters.keys())
                    default_params = all_params - provided_params
                    default_values = []
                    for name in default_params:
                        p = sig.parameters[name]
                        if p.default is not inspect._empty:  # type: ignore[attr-defined]
                            default_values.append(_format_default(p))
                    if default_values:
                        logger.info("Using defaults for: " + ", ".join(default_values))
                elif sig.parameters:
                    logger.info("All parameters will use their default values")
            except Exception as e:  # pragma: no cover - best effort logging
                logger.debug(f"Could not inspect environment load function signature: {e}")

            logger.debug(f"Calling {module_name}.load_environment with {len(env_args)} arguments")
            env_instance = env_load_func(**env_args)
            if not isinstance(env_instance, IEnvironment):
                logger.warning(f"Object returned by {module_name}.load_environment is not an IEnvironment; got {type(env_instance).__name__}")
            logger.info(f"Successfully loaded environment {env_path} as {type(env_instance).__name__}")
            return env_instance

        # Path B: find a subclass of IEnvironment and instantiate directly
        env_class = _pick_env_class(module, class_name)
        try:
            sig = inspect.signature(env_class)
            defaults_info = [_format_default(param) for param in list(sig.parameters.values())[1:]]  # skip 'self'
            if defaults_info:
                logger.debug(f"Constructor defaults for {env_class.__name__}: " + ", ".join(defaults_info))
        except Exception as e:  # pragma: no cover - best effort logging
            logger.debug(f"Could not inspect constructor signature: {e}")

        # Validate required parameters
        missing_required = []
        try:
            sig = inspect.signature(env_class)
            for name, p in list(sig.parameters.items())[1:]:  # skip 'self'
                if p.default is inspect._empty and name not in env_args:
                    missing_required.append(name)
        except Exception:
            # If we cannot inspect, attempt best-effort construction
            pass

        if missing_required:
            raise TypeError(f"Missing required init params for {env_class.__name__}: {', '.join(missing_required)}")

        env_instance = env_class(**env_args)
        logger.info(f"Successfully loaded environment {env_path} as {env_instance.__class__.__name__}")
        return env_instance

    except ImportError as e:
        error_message = f"Could not import '{env_path}' environment. Ensure the package/module '{module_name}' is importable.\n{e}"
        logger.error(error_message)
        raise ValueError(error_message) from e
    except Exception as e:
        error_message = f"Failed to load environment {env_path} with args {env_args}: {str(e)}"
        logger.error(error_message)
        raise RuntimeError(error_message) from e
