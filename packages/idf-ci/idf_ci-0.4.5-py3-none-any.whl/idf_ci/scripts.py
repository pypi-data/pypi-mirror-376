# SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0
import logging
import os
import typing as t
from dataclasses import dataclass

from idf_build_apps import App, build_apps, find_apps
from idf_build_apps.constants import BuildStatus
from idf_build_apps.manifest import DEFAULT_BUILD_TARGETS
from idf_build_apps.utils import get_parallel_start_stop

from ._compat import UNDEF, UndefinedOr, is_defined_and_satisfies, is_undefined
from .envs import GitlabEnvVars
from .settings import CiSettings

logger = logging.getLogger(__name__)


@dataclass
class ProcessedArgs:
    """Container for processed arguments with meaningful field names."""

    modified_files: t.Optional[t.List[str]]
    modified_components: t.Optional[t.List[str]]
    filter_expr: t.Optional[str]
    default_build_targets: t.List[str]
    test_related_apps: t.Optional[t.List[App]]
    non_test_related_apps: t.Optional[t.List[App]]


def preprocess_args(
    modified_files: t.Optional[t.List[str]] = None,
    modified_components: t.Optional[t.List[str]] = None,
    filter_expr: t.Optional[str] = None,
    default_build_targets: t.Optional[t.List[str]] = None,
) -> ProcessedArgs:
    """Set values according to the environment variables, .toml settings, and defaults.

    :param modified_files: List of modified files
    :param modified_components: List of modified components
    :param filter_expr: Pytest filter expression
    :param default_build_targets: Default build targets to use

    :returns: Processed arguments as a ProcessedArgs object
    """
    envs = GitlabEnvVars()
    settings = CiSettings()

    processed_targets = DEFAULT_BUILD_TARGETS.get() if default_build_targets is None else default_build_targets
    if settings.extra_default_build_targets:
        processed_targets = [*processed_targets, *settings.extra_default_build_targets]

    if envs.select_all_pytest_cases:
        processed_files = None
        processed_components = None
        processed_filter = None
    else:
        processed_files = modified_files
        if processed_files is None and is_defined_and_satisfies(envs.CHANGED_FILES_SEMICOLON_SEPARATED):
            processed_files = envs.CHANGED_FILES_SEMICOLON_SEPARATED.split(';')  # type: ignore

        processed_components = modified_components
        if processed_files is not None and processed_components is None:
            processed_components = sorted(settings.get_modified_components(processed_files))

        processed_filter = envs.IDF_CI_SELECT_BY_FILTER_EXPR if filter_expr is None else filter_expr
        if processed_filter is not None:
            logger.info(
                'Running with quick test filter: %s. Skipping dependency-driven build. '
                'Build and test only filtered cases.',
                processed_filter,
            )
            processed_files = None
            processed_components = None

    if not settings.is_in_ci:
        test_related_apps: t.Optional[t.List[App]] = None
        non_test_related_apps: t.Optional[t.List[App]] = None
    else:
        logger.debug('Running in CI, reading test-related and non-test-related apps from files if available')
        test_related_apps = settings.read_apps_from_files([settings.collected_test_related_apps_filepath])
        non_test_related_apps = settings.read_apps_from_files([settings.collected_non_test_related_apps_filepath])

        # if one of the two is None, it should be empty list
        if test_related_apps is None and non_test_related_apps is not None:
            test_related_apps = []
        elif test_related_apps is not None and non_test_related_apps is None:
            non_test_related_apps = []

    return ProcessedArgs(
        modified_files=processed_files,
        modified_components=processed_components,
        filter_expr=processed_filter,
        default_build_targets=processed_targets,
        test_related_apps=test_related_apps,
        non_test_related_apps=non_test_related_apps,
    )


def get_all_apps(
    *,
    paths: t.Optional[t.List[str]] = None,
    target: str = 'all',
    # args that may be set by env vars or .idf_ci.toml
    modified_files: t.Optional[t.List[str]] = None,
    modified_components: t.Optional[t.List[str]] = None,
    filter_expr: t.Optional[str] = None,
    default_build_targets: t.Optional[t.List[str]] = None,
    # args that may be set by target
    marker_expr: UndefinedOr[t.Optional[str]] = UNDEF,
    # additional args
    compare_manifest_sha_filepath: t.Optional[str] = None,
    build_system: UndefinedOr[t.Optional[str]] = UNDEF,
) -> t.Tuple[t.List[App], t.List[App]]:
    """Get test-related and non-test-related applications.

    :param paths: List of paths to search for applications
    :param target: Target device(s) separated by commas
    :param modified_files: List of modified files
    :param modified_components: List of modified components
    :param filter_expr: Pytest filter expression -k
    :param default_build_targets: Default build targets to use
    :param marker_expr: Pytest marker expression -m
    :param compare_manifest_sha_filepath: Path to the manifest SHA file generated by
        `idf-build-apps dump-manifest-sha`
    :param build_system: Filter the apps by build system. Can be "cmake", "make" or a
        custom App class path

    :returns: Tuple of (test_related_apps, non_test_related_apps)
    """
    settings = CiSettings()
    processed_args = preprocess_args(
        modified_files=modified_files,
        modified_components=modified_components,
        filter_expr=filter_expr,
        default_build_targets=default_build_targets,
    )

    if processed_args.test_related_apps is not None and processed_args.non_test_related_apps is not None:
        for app in processed_args.test_related_apps:
            app.preserve = settings.preserve_test_related_apps

        for app in processed_args.non_test_related_apps:
            app.preserve = settings.preserve_non_test_related_apps

        return processed_args.test_related_apps, processed_args.non_test_related_apps

    additional_kwargs: t.Dict[str, t.Any] = {
        'compare_manifest_sha_filepath': compare_manifest_sha_filepath,
        'build_system': build_system,
    }
    if is_undefined(build_system):
        additional_kwargs.pop('build_system')

    if settings.exclude_dirs:
        additional_kwargs['exclude'] = settings.exclude_dirs

    apps = []
    for _t in target.split(','):
        if _t != 'all' and _t not in processed_args.default_build_targets:
            _default_build_targets = [*processed_args.default_build_targets, _t]
        else:
            _default_build_targets = processed_args.default_build_targets

        apps.extend(
            find_apps(
                paths or ['.'],
                _t,
                modified_files=processed_args.modified_files,
                modified_components=processed_args.modified_components,
                include_skipped_apps=True,
                default_build_targets=_default_build_targets,
                **additional_kwargs,
            )
        )

    # avoid circular import
    from .idf_pytest import get_pytest_cases

    cases = get_pytest_cases(
        paths=paths, target=target, marker_expr=marker_expr, filter_expr=processed_args.filter_expr
    )
    if not cases:
        for app in apps:
            app.preserve = settings.preserve_non_test_related_apps
        return [], sorted(apps)

    # Get modified pytest cases if any
    modified_pytest_cases = []
    if processed_args.modified_files:
        modified_pytest_scripts = [
            os.path.dirname(f) for f in processed_args.modified_files if os.path.splitext(f)[1] == '.py'
        ]
        if modified_pytest_scripts:
            modified_pytest_cases = get_pytest_cases(
                paths=modified_pytest_scripts,
                target=target,
                marker_expr=marker_expr,
                filter_expr=processed_args.filter_expr,
            )

    # Create dictionaries mapping app info to test cases
    def get_app_dict(_cases):
        return {(case_app.path, case_app.target, case_app.config): _case for _case in _cases for case_app in _case.apps}

    pytest_dict = get_app_dict(cases)
    modified_pytest_dict = get_app_dict(modified_pytest_cases)

    test_apps = set()
    non_test_apps = set()

    for app in apps:
        app_key = (os.path.abspath(app.app_dir), app.target, app.config_name or 'default')
        # override build_status if test script got modified
        case = modified_pytest_dict.get(app_key)
        if case:
            test_apps.add(app)
            app.build_status = BuildStatus.SHOULD_BE_BUILT
            logger.debug('Found app: %s - required by modified test case %s', app, case.path)
        elif app.build_status != BuildStatus.SKIPPED:
            case = pytest_dict.get(app_key)
            if case:
                test_apps.add(app)
                # build or not should be decided by the build stage
                logger.debug('Found test-related app: %s - required by %s', app, case.path)
            else:
                non_test_apps.add(app)
                logger.debug('Found non-test-related app: %s', app)

    for app in test_apps:
        app.preserve = settings.preserve_test_related_apps

    for app in non_test_apps:
        app.preserve = settings.preserve_non_test_related_apps

    return sorted(test_apps), sorted(non_test_apps)


def build(
    *,
    paths: t.Optional[t.List[str]] = None,
    target: str = 'all',
    parallel_count: int = 1,
    parallel_index: int = 1,
    modified_files: t.Optional[t.List[str]] = None,
    modified_components: t.Optional[t.List[str]] = None,
    only_test_related: t.Optional[bool] = None,
    only_non_test_related: t.Optional[bool] = None,
    dry_run: bool = False,
    build_system: UndefinedOr[str] = UNDEF,
    marker_expr: UndefinedOr[str] = UNDEF,
    filter_expr: t.Optional[str] = None,
) -> t.Tuple[t.List[App], int]:
    """Build applications based on specified parameters.

    :param paths: List of paths to search for applications
    :param target: Target device(s) separated by commas
    :param parallel_count: Total number of parallel jobs
    :param parallel_index: Index of current parallel job (1-based)
    :param modified_files: List of modified files
    :param modified_components: List of modified components
    :param only_test_related: Only build test-related applications
    :param only_non_test_related: Only build non-test-related applications
    :param dry_run: Do not actually build, just simulate
    :param build_system: Filter the apps by build system. Can be "cmake", "make" or a
        custom App class path
    :param marker_expr: Pytest marker expression
    :param filter_expr: Filter expression

    :returns: Tuple of (built apps, build return code)
    """
    settings = CiSettings()
    envs = GitlabEnvVars()

    # Preprocess arguments
    processed_args = preprocess_args(
        modified_files=modified_files,
        modified_components=modified_components,
        filter_expr=filter_expr,
    )

    test_related_apps, non_test_related_apps = get_all_apps(
        paths=paths,
        target=target,
        modified_files=processed_args.modified_files,
        modified_components=processed_args.modified_components,
        build_system=build_system,
        marker_expr=marker_expr,
        filter_expr=processed_args.filter_expr,
    )

    for app in test_related_apps:
        app.preserve = settings.preserve_test_related_apps

    for app in non_test_related_apps:
        app.preserve = settings.preserve_non_test_related_apps

    if processed_args.filter_expr:
        only_test_related = True
        logger.debug(
            'Filter expression is set to `%s`, building only test-related applications', processed_args.filter_expr
        )
    if is_defined_and_satisfies(marker_expr):
        only_test_related = True
        logger.debug('Marker expression is set to `%s`, building only test-related applications', marker_expr)

    if only_test_related is True or (only_test_related is None and envs.IDF_CI_BUILD_ONLY_TEST_RELATED_APPS):
        logger.info('Building only test-related applications')
        apps = test_related_apps
    elif only_non_test_related is True or (
        only_non_test_related is None and envs.IDF_CI_BUILD_ONLY_NON_TEST_RELATED_APPS
    ):
        logger.info('Building only non-test-related applications')
        apps = non_test_related_apps
    else:
        logger.info('Building all applications')
        apps = sorted([*test_related_apps, *non_test_related_apps])

    ret = build_apps(
        apps,
        parallel_count=parallel_count,
        parallel_index=parallel_index,
        dry_run=dry_run,
        modified_files=processed_args.modified_files,
        modified_components=processed_args.modified_components,
    )

    # only returning the ones assigned, 1-indexed
    start, stop = get_parallel_start_stop(len(apps), parallel_count, parallel_index)

    return apps[start - 1 : stop], ret
