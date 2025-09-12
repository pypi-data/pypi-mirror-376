import json
import os
import shlex
import subprocess
from collections.abc import Iterable

import click


def _parse_accounts_json(accounts_str: str) -> list[str]:
    """
    Parse accounts strictly as a JSON list of strings.
    Example: '["111111111111","222222222222"]'
    """
    try:
        data = json.loads(accounts_str)
    except Exception as e:
        raise click.ClickException(f"Invalid JSON for accounts: {e}")
    if not isinstance(data, list):
        raise click.ClickException("Accounts must be a JSON list of strings")
    return [str(x).strip() for x in data if str(x).strip()]


@click.command("aws-each", context_settings={"ignore_unknown_options": True})
@click.option(
    "--accounts",
    envvar="TARGET_ACCOUNTS",
    required=True,
    help='JSON list of AWS account IDs (e.g. \'["111111111111","222222222222"]\').',
)
@click.option(
    "--role-name",
    default="github-actions-backend-role",
    show_default=True,
    help="IAM Role name to assume in each target account.",
)
@click.option(
    "--role-arn-template",
    default="arn:aws:iam::{account}:role/{role_name}",
    show_default=True,
    help="Template for the role ARN. {account} and {role_name} will be formatted.",
)
@click.option(
    "--session-name",
    default="pevx-aws-each",
    show_default=True,
    help="STS session name.",
)
@click.option(
    "--duration-seconds",
    default=3600,
    show_default=True,
    type=int,
    help="STS session duration in seconds.",
)
@click.option(
    "--region",
    default=None,
    help="AWS region to export for the sub-command (falls back to $AWS_REGION).",
)
@click.option(
    "--continue-on-error/--fail-fast",
    default=False,
    show_default=True,
    help="Continue with remaining accounts when a command fails.",
)
@click.argument("aws_args", nargs=-1, type=click.UNPROCESSED)
def aws_each(
    accounts: str,
    role_name: str,
    role_arn_template: str,
    session_name: str,
    duration_seconds: int,
    region: str,
    continue_on_error: bool,
    aws_args: Iterable[str],
):
    """
    Assume a role in EACH target account (from JSON list) and run the provided AWS CLI command.

    Usage:

      TARGET_ACCOUNTS='["111111111111","222222222222"]'
      pevx aws-each ssm put-parameter --name "/path/{account}" --value "$IMAGE" --type String --overwrite
    """
    acct_list = _parse_accounts_json(accounts)
    if not aws_args:
        raise click.ClickException("You must provide an AWS CLI command.")

    region = region or os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")

    base_env = os.environ.copy()
    overall_rc = 0

    for acct in acct_list:
        role_arn = role_arn_template.format(account=acct, role_name=role_name)
        click.echo(f"=== Assuming role in {acct} -> {role_arn} ===")

        try:
            sts_cmd = [
                "aws",
                "sts",
                "assume-role",
                "--role-arn",
                role_arn,
                "--role-session-name",
                session_name,
                "--duration-seconds",
                str(duration_seconds),
            ]
            sts = subprocess.run(sts_cmd, check=True, capture_output=True, text=True, env=base_env)
            data = json.loads(sts.stdout)
            creds = data.get("Credentials") or {}

            akid, secret, token = (
                creds.get("AccessKeyId"),
                creds.get("SecretAccessKey"),
                creds.get("SessionToken"),
            )
            if not (akid and secret and token):
                raise click.ClickException("AssumeRole response did not contain credentials.")

            acct_env = base_env.copy()
            acct_env["AWS_ACCESS_KEY_ID"] = akid
            acct_env["AWS_SECRET_ACCESS_KEY"] = secret
            acct_env["AWS_SESSION_TOKEN"] = token
            if region:
                acct_env["AWS_DEFAULT_REGION"] = region

            rendered_args = [a.format(account=acct) for a in aws_args]
            click.echo(f"Running: {shlex.join(['aws', *rendered_args])}")

            run = subprocess.run(["aws", *rendered_args], env=acct_env)
            if run.returncode != 0:
                msg = f"[{acct}] Command failed with exit code {run.returncode}."
                if continue_on_error:
                    click.echo("WARN: " + msg, err=True)
                    overall_rc = run.returncode
                    continue
                raise click.ClickException(msg)

            click.echo(f"[{acct}] ✅ Success")

        except subprocess.CalledProcessError as e:
            msg = f"[{acct}] Subprocess error: {e}"
            if continue_on_error:
                click.echo("WARN: " + msg, err=True)
                overall_rc = e.returncode or 1
                continue
            raise click.ClickException(msg)

    if overall_rc != 0:
        raise SystemExit(overall_rc)
