import asyncio
import logging

import cog
import disnake
from utils import shortcuts

log = logging.getLogger(__name__)

REMINDER_CHOICES = [
    "30 секунд",
    "1 минута",
    "5 минут",
    "10 минут",
    "30 минут",
    "1 час",
    "3 часа",
    "5 часов",
    "10 часов",
    "15 часов",
    "17 часов",
    "1 день",
]

REMINDER_SECONDS = {
    "30 секунд": 30,
    "1 минута": 60,
    "5 минут": 300,
    "10 минут": 600,
    "30 минут": 1800,
    "1 час": 3600,
    "3 часа": 10800,
    "5 часов": 18000,
    "10 часов": 36000,
    "15 часов": 54000,
    "17 часов": 61200,
    "1 день": 86400,
}


class Reminder(cog.Cog):
    def __init__(self, bot: cog.KisaBot):
        self.bot = bot

    @cog.slash_command(
        name="reminder",
        description=cog.Localised("Set a reminder", key="reminder_desc"),
    )
    async def timer(
        self,
        inter: cog.ApplicationCommandInteraction,
        remind: str = cog.Param(description="О чём напомнить"),
        time: str = cog.Param(
            description="Через сколько напомнить (в личные сообщения)",
            autocomplete=cog.sh.generate_autocomplete_choices(REMINDER_CHOICES),
        ),
    ):
        await inter.response.defer(ephemeral=True)
        sec = REMINDER_SECONDS.get(time)
        if sec is None:
            await inter.edit_original_response(
                await cog.sh.tbc(inter, "Неизвестный интервал времени.")
            )
            return

        await inter.edit_original_response(
            await cog.sh.tbc(
                inter,
                f"Установила напоминание: `{remind}` {self.bot.custom_emojis.icon_alarm}\n"
                f"Напомню через {time} вам в личные сообщения",
            )
        )

        now = shortcuts.now_datetime()
        log.info(
            "reminder set user=%s interval=%s text=%s at=%s",
            inter.author.id,
            time,
            remind[:200],
            now.isoformat(),
        )

        await asyncio.sleep(sec)

        title = self.bot.custom_emojis.icon_alarm + await cog.sh.tbc(
            inter, " | Напоминаю!"
        )
        embed = cog.Embed(title=title, description=remind, color=0xFFFF80)
        try:
            await inter.author.send(inter.author.mention, embed=embed)
        except disnake.Forbidden:
            pass
        log.info("reminder done user=%s", inter.author.id)


def setup(bot):
    bot.add_cog(Reminder(bot))
    bot.cog_reload(__name__)
