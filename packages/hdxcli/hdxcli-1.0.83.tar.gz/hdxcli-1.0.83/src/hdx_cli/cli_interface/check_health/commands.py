import click

from hdx_cli.cli_interface.common.click_extensions import HdxCommand
from hdx_cli.cli_interface.common.undecorated_click_commands import basic_update
from hdx_cli.library_api.common.exceptions import ResourceNotFoundException
from hdx_cli.library_api.common.generic_resource import access_resource_detailed
from hdx_cli.library_api.common.logging import get_logger
from hdx_cli.library_api.utility.decorators import report_error_and_exit, ensure_logged_in
from hdx_cli.models import ProfileUserContext
from . import const, utils
from .cleaner import table as table_cleaner

logger = get_logger()


@click.command(cls=HdxCommand, name="check-health")
@click.argument(
    "project_name",
    metavar="PROJECT_NAME",
    required=False,
    default=None,
)
@click.argument(
    "table_name",
    metavar="TABLE_NAME",
    required=False,
    default=None,
)
@click.option(
    "--repair",
    is_flag=True,
    default=False,
    help="Attempt to automatically repair detected issues.",
)
@click.pass_context
@report_error_and_exit(exctype=Exception)
@ensure_logged_in
def check_health(
    ctx: click.Context,
    project_name: str,
    table_name: str,
    repair: bool,
):
    """Check the integrity of transforms and autoviews.
    This command inspects transforms and autoviews for common integrity
    issues, such as datatype mismatches.

    \b
    **Usage Scenarios**:
    - No arguments: Checks all transforms in all projects.
    - With `PROJECT_NAME`: Limits the check to a specific project.
    - With `PROJECT_NAME` and `TABLE_NAME`: Limits the check to a single table.

    The `--repair` flag will attempt to automatically fix any detected issues
    that are safely repairable.

    \b
    Examples:
      # Check the entire organization
      {full_command_prefix} check-health

    \b
      # Check a specific project and attempt to repair issues
      {full_command_prefix} check-health my_project --repair

    \b
      # Check a single table within a project
      {full_command_prefix} check-health my_project my_table
    """
    parent = getattr(ctx, "parent")
    if parent is None:
        return
    profile = parent.obj["usercontext"]
    if project_name and table_name:
        click.echo(
            f"Checking health of transforms in project '{project_name}' and table '{table_name}'..."
        )
    elif project_name:
        click.echo(f"Checking health of transforms in project '{project_name}'...")
    else:
        click.echo("Checking health of transforms for the entire org...")

    _check_health(profile, project_name, table_name, repair)


def _check_health(
    profile: ProfileUserContext,
    target_project_name: str,
    target_table_name: str,
    repair: bool,
):
    """Check the integrity of transforms and auto-views in a Hydrolix cluster"""
    projects, _ = access_resource_detailed(profile, [("projects", target_project_name)])
    # If 'target_project_name' is not provided, projects will contain a list of all projects in the org
    # If 'target_project_name' is provided, projects will contain a simple dict with the project details
    projects = [projects] if isinstance(projects, dict) else projects
    if not projects:
        logger.info("[INFO] Cluster is healthy — There are no projects")
        return

    for project in projects:
        project_name = project.get("name", "")
        utils.print_header(f"Project — {project_name}", underline_char="+")

        tables, _ = access_resource_detailed(
            profile, [("projects", project_name), ("tables", target_table_name)]
        )
        # If 'target_table_name' is not provided, tables will contain a list of all tables in the project
        # If 'target_table_name' is provided, tables will contain a simple dict with the table details
        tables = [tables] if isinstance(tables, dict) else tables
        if not tables:
            logger.info(f"\n[INFO] Project '{project_name}' has no tables")
            continue

        for table in tables:
            table_name = table.get("name")
            utils.print_header(f"Table — {table_name}", underline_char="+")
            table_settings = table.get("settings", {})
            table_summary_settings = table_settings.get("summary", None)
            if table_summary_settings:
                logger.info(
                    f"\n[INFO] Table '{project_name}.{table_name}' is summary table. Skipping"
                )
                continue
            auto_view = _load_auto_view(profile, project_name, table_name)
            transforms = _load_transforms(profile, project_name, table_name)
            if (not transforms) and (not auto_view):
                logger.info(
                    f"\n[INFO] Table '{project_name}.{table_name}' skipped — no auto_view or transforms"
                )
                continue

            if repair:
                cleaner = table_cleaner.TableCleaner(
                    table=table,
                    transforms=transforms,
                    auto_view=auto_view,
                )
                _repair(profile, cleaner, project, table)
                auto_view = _load_auto_view(profile, project_name, table_name)
                transforms = _load_transforms(profile, project_name, table_name)
            cleaner = table_cleaner.TableCleaner(
                table=table,
                transforms=transforms,
                auto_view=auto_view,
            )
            cleaner.print_reports()


def _repair(profile, cleaner, project, table):
    """Actually repair the broken transforms"""
    if cleaner.repair_is_possible and cleaner.repair_is_necessary:
        logger.info("[INFO] Table needs repair")
        project_id = project.get(const.FIELD_UUID)
        table_id = table.get(const.FIELD_UUID)
        corrected_auto_view = cleaner.corrected_autoview
        if corrected_auto_view:
            logger.info("[INFO] Repairing autoview")
            auto_view_id = corrected_auto_view.get(const.FIELD_UUID)
            _update_view(profile, project_id, table_id, auto_view_id, corrected_auto_view)
        else:
            logger.info("[INFO] Autoview does not need repair")

        # Repair the transforms
        for transform_id, corrected_transform in cleaner.corrected_transforms.items():
            repairing_transform_name = corrected_transform.get(const.FIELD_NAME)
            logger.info(f"[INFO] Repairing transform {repairing_transform_name}")
            _update_transform(profile, project_id, table_id, transform_id, corrected_transform)
        logger.info("[INFO] Table repair completed")
    elif cleaner.repair_is_necessary:
        logger.info("[ERROR] This table has issues which must be repaired manually")
    else:
        logger.info("[INFO] This table does not need to be repaired.")


def _load_auto_view(profile, project_name, table_name):
    """Get the view and tables, and build a cleaner"""

    try:
        auto_view, _ = access_resource_detailed(
            profile,
            [
                ("projects", project_name),
                ("tables", table_name),
                ("views", const.AUTO_VIEW_NAME),
            ],
        )
    except ResourceNotFoundException:
        auto_view = {}
    return auto_view


def _load_transforms(profile, project_name, table_name):
    transforms, _ = access_resource_detailed(
        profile,
        [
            ("projects", project_name),
            ("tables", table_name),
            ("transforms", None),
        ],
    )
    return transforms


def _update_view(profile, project_id, table_id, view_id, correct_view_body):
    """Update a view"""
    org_id = profile.org_id
    resource_path = (
        f"/config/v1/orgs/{org_id}/projects/{project_id}/tables/{table_id}/views/{view_id}/"
    )
    return basic_update(profile, resource_path, body=correct_view_body, force_operation="true")


def _update_transform(profile, project_id, table_id, transform_id, correct_transform_body):
    """Update a transform"""
    org_id = profile.org_id
    resource_path = f"/config/v1/orgs/{org_id}/projects/{project_id}/tables/{table_id}/transforms/{transform_id}/"
    return basic_update(profile, resource_path, body=correct_transform_body, force_operation="true")
