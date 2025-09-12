import logging
import re

from slack_bolt.async_app import AsyncApp
from slack_sdk.web.async_client import AsyncWebClient

from hygroup.gateway.slack.app_home.preferences.handlers import UserPreferenceConfigHandlers
from hygroup.gateway.slack.app_home.secrets.handlers import SecretConfigHandlers
from hygroup.gateway.slack.app_home.views import HomeViewBuilder
from hygroup.user.secrets import SecretsStore
from hygroup.user.settings import SettingsStore


class SlackHomeHandlers:
    """Handles Slack App Home interactions for user and system-wide configuration management.

    Args:
        client: Slack Web API client for making API calls
        app: Slack Bolt app instance for registering event handlers
        system_editor_ids: List of Slack user IDs authorized to edit system-wide settings.
            If None, all users can edit system configurations.
    """

    def __init__(
        self,
        client: AsyncWebClient,
        app: AsyncApp,
        secrets_store: SecretsStore,
        settings_store: SettingsStore,
        system_editor_ids: list[str] | None = None,
    ):
        self._client = client
        self._app = app
        self._system_editor_ids = system_editor_ids
        self._slack_user_mapping = settings_store.get_mapping("slack")

        self._secret_config_handlers = SecretConfigHandlers(client, secrets_store, self._resolve_system_user_id)
        self._user_preference_config_handlers = UserPreferenceConfigHandlers(
            client, settings_store, self._resolve_system_user_id
        )

        self._app_name: str | None = None
        self._logger = logging.getLogger(__name__)

    def _resolve_system_user_id(self, slack_user_id: str) -> str:
        return self._slack_user_mapping.get(slack_user_id, slack_user_id)

    def register(self):
        # Home page handlers
        self._app.event("app_home_opened")(self.handle_app_home_opened)

        # User secret handlers
        self._app.action("home_add_user_secret")(self._secret_config_handlers.handle_add_user_secret)
        self._app.view("home_user_secret_added_view")(
            self.refresh_home_after_completion(self._secret_config_handlers.handle_user_secret_added)
        )
        self._app.action(re.compile(r"^home_user_secret_var_menu:"))(
            self._secret_config_handlers.handle_user_secret_menu
        )
        self._app.view("home_user_secret_edited_view")(
            self.refresh_home_after_completion(self._secret_config_handlers.handle_user_secret_edited)
        )
        self._app.view("home_user_secret_delete_confirm_view")(
            self.refresh_home_after_completion(self._secret_config_handlers.handle_user_secret_delete_confirmed)
        )

        # User preference handlers
        self._app.action("home_user_preferences_overflow")(
            self._user_preference_config_handlers.handle_user_preferences_overflow
        )
        self._app.action("home_user_preferences_create")(
            self._user_preference_config_handlers.handle_user_preferences_create
        )
        self._app.view("home_user_preferences_edited_view")(
            self.refresh_home_after_completion(self._user_preference_config_handlers.handle_user_preferences_edited)
        )
        self._app.view("home_user_preferences_delete_confirm_view")(
            self.refresh_home_after_completion(
                self._user_preference_config_handlers.handle_user_preferences_delete_confirmed
            )
        )

        self._logger.info("All handlers registered")

    async def handle_app_home_opened(self, client, event, logger):
        try:
            user_id = event["user"]
            await self.refresh_home_view(user_id)
        except Exception as e:
            self._logger.error(f"Error handling app home opened: {e}")

    async def refresh_home_view(self, user_id: str):
        try:
            app_name = await self._get_app_display_name()
            username = await self._get_user_display_name(user_id)
            user_secrets = await self._secret_config_handlers.get_user_secrets(user_id)
            user_preferences = await self._user_preference_config_handlers._get_user_preferences(user_id)

            view = HomeViewBuilder.build_home_view(
                app_name=app_name,
                username=username,
                user_secrets=user_secrets,
                user_preferences=user_preferences,
            )

            await self._client.views_publish(user_id=user_id, view=view)
        except Exception as e:
            self._logger.error(f"Error refreshing home view for {user_id}: {e}")

    def _is_system_editor(self, user_id: str) -> bool:
        if self._system_editor_ids is None:
            return True
        return user_id in self._system_editor_ids

    async def _get_user_display_name(self, user_id: str) -> str:
        try:
            response = await self._client.users_info(user=user_id)
            user_profile = response["user"]["profile"]
            return user_profile.get("display_name") or user_profile.get("real_name") or user_profile.get("name", "User")
        except Exception as e:
            self._logger.error(f"Error fetching user info for {user_id}: {e}")
            return "User"

    async def _get_app_display_name(self) -> str | None:
        if self._app_name is None:
            try:
                auth_response = await self._client.auth_test()
                bot_user_id = auth_response["user_id"]

                user_info = await self._client.users_info(user=bot_user_id)
                bot_profile = user_info["user"]["profile"]

                self._app_name = bot_profile.get("display_name") or bot_profile.get("real_name")
            except Exception as e:
                self._logger.error(f"Error fetching app display name: {e}")
                return None

        return self._app_name

    def require_system_edit_permission(self, handler):
        async def wrapper(ack, body, client, *args, **kwargs):
            user_id = body["user"]["id"]
            if not self._is_system_editor(user_id):
                await ack()
                self._logger.warning(f"User {user_id} attempted to edit system config without permission")
                return
            return await handler(ack, body, client, *args, **kwargs)

        return wrapper

    def refresh_home_after_completion(self, handler):
        async def wrapper(ack, body, client, view, logger, *args, **kwargs):
            result = await handler(ack, body, client, view, logger, *args, **kwargs)
            await self.refresh_home_view(body["user"]["id"])
            return result

        return wrapper
