import click
from sigmate.utils.logger import Logger
from sigmate.cli.sign import sign_cmd
from sigmate.cli.verify import verify_cmd
from sigmate.cli.trust import trust_cmd
from sigmate.cli.clean import clean_cmd
from sigmate.cli.configure import configure_cmd


@click.group()
@click.option("--debug", is_flag=True)
@click.option("--no-emojis", "-ne", is_flag=True, help="Disable emoji output")
@click.pass_context
def cli(ctx, debug, no_emojis):
    ctx.ensure_object(dict)
    ctx.obj["logger"] = Logger(enabled=debug, emojis=not no_emojis)


cli.add_command(sign_cmd, name="sign")
cli.add_command(verify_cmd, name="verify")
cli.add_command(trust_cmd, name="trust")
cli.add_command(clean_cmd, name="clean")
cli.add_command(configure_cmd, name="configure")
