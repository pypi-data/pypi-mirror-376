# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "invoke",
# ]
# ///
from invoke import task
from invoke.context import Context


@task()
def licences(ctx: Context, only_failing: bool = False):
    """Checks licenses"""
    args = ""
    if only_failing:
        args = f"{args} --show-only-failing"
    ctx.run(f"uvx licensecheck {args}", pty=True)
