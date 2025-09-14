import click
from pathlib import Path
from typing import Optional

from sigmate.managers.config import ConfigManager
from sigmate.utils.logger import Logger
from sigmate.utils.git import get_git_author


@click.command("configure")
@click.option(
    "--private-key-path",
    "priv_key_path_arg",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True, allow_dash=False),
    help="Set the default private key path for signing.",
    default=None,
)
@click.option(
    "--signer-identity",
    "signer_identity_arg",
    type=str,
    help="Set the default signer identity (e.g., 'Name <email@host.com>').",
    default=None,
)
@click.option(
    "--keyring-path",
    "keyring_path_arg",
    type=click.Path(file_okay=False, resolve_path=True, allow_dash=False),
    help="Set the default public key keyring path.",
    default=None,
)
@click.pass_context
def configure_cmd(
    ctx: click.Context,
    priv_key_path_arg: Optional[str],
    signer_identity_arg: Optional[str],
    keyring_path_arg: Optional[str],
):
    """
    Configure default settings for sigmate.

    Run with arguments to set values directly, or run without arguments
    for an interactive setup session.
    """
    logger: Logger = ctx.obj["logger"]
    config_manager = ConfigManager()
    is_non_interactive = any([priv_key_path_arg, signer_identity_arg, keyring_path_arg])

    if is_non_interactive:
        logger.info("Updating configuration non-interactively...", emoji="🤖")
        if priv_key_path_arg:
            config_manager.set("private_key_path", priv_key_path_arg)
            logger.success(
                f"Default private key set to: {priv_key_path_arg}", emoji="🔑"
            )

        if signer_identity_arg:
            config_manager.set("signer_identity", signer_identity_arg)
            logger.success(
                f"Default signer identity set to: {signer_identity_arg}", emoji="👤"
            )

        if keyring_path_arg:
            config_manager.set("keyring_path", keyring_path_arg)
            logger.success(f"Keyring path set to: {keyring_path_arg}", emoji="📂")

    else:
        logger.info("Configuring Sigmate User Defaults (Interactive)", emoji="⚙️")
        logger.info(
            f"Configuration will be saved to: {config_manager.config_path}", emoji=""
        )

        logger.info("\n--- Signer Profile ---", emoji="")
        priv_key_path_str = click.prompt(
            "Enter path to your default private key for signing",
            default=config_manager.get("private_key_path", ""),
            type=click.Path(
                exists=True, dir_okay=False, resolve_path=True, allow_dash=False
            ),
            show_default=True,
        )
        config_manager.set("private_key_path", priv_key_path_str)

        git_author = get_git_author()
        identity_prompt_default = git_author or config_manager.get(
            "signer_identity", ""
        )

        signer_id_str = click.prompt(
            "Enter your default signer identity",
            default=identity_prompt_default,
            show_default=True,
        )
        config_manager.set("signer_identity", signer_id_str)

        logger.info("\n--- Keyring Settings ---", emoji="")
        keyring_path_str = click.prompt(
            "Enter path for your public key keyring directory",
            default=config_manager.get("keyring_path", ""),
            type=click.Path(file_okay=False, resolve_path=True, allow_dash=False),
            show_default=True,
        )
        config_manager.set("keyring_path", keyring_path_str)

    try:
        config_manager.save()
        logger.success("Configuration saved successfully!", emoji="✅")
    except IOError as e:
        raise click.ClickException(f"Failed to save configuration: {e}")
