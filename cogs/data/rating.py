import cog
from disnake.ext.commands import BucketType, cooldown
from utils import config


class Rating(cog.Cog):
  def __init__(self, bot: cog.MemeismBot):
    self.bot = bot

  @cog.slash_command(name="rating")
  async def rating(self, inter: cog.ApplicationCommandInteraction):
    pass

  @rating.sub_command(
    name="view",
    description=cog.Localised("Look at someone else's or your rating", key="rating_view_desc"),
  )
  async def view(
    self,
    inter: cog.ApplicationCommandInteraction,
    view: cog.Member = cog.Param(description="Чей рейтинг смотрим"),
  ):
    await inter.response.defer(ephemeral=True)

    ratings = await self.bot.database.readSocialRating(
      user_id=view.id
    )
    if not ratings:
      await self.bot.database.createSocialRating(view.id, 0)
      
      ratings = await self.bot.database.readSocialRating(
        user_id=view.id,
        cacheOverwrite=True
      )
    
    ratingRecord = ratings[0]
    
    color = 0x1ED860 if ratingRecord.rating > 0 else 0xDF4E4E
    embed = cog.Embed(
      title=await cog.shortcuts.tbc(inter, f"Рейтинг {view.display_name}"),
      description=f"## {ratingRecord.rating}",
      color=color,
    ).set_thumbnail(url=view.display_avatar.url)
    await inter.edit_original_response(embed=embed)

  @cooldown(1, 43200, BucketType.user)
  @rating.sub_command(
    name="add",
    description=cog.Localised("Up someones rating", key="rating_add_desc"),
  )
  async def add(
    self,
    inter: cog.ApplicationCommandInteraction,
    view: cog.Member = cog.Param(description="Чей рейтинг поднимаем"),
  ):
    await inter.response.defer(ephemeral=True)
    if view == inter.author:
      await inter.edit_original_response(
        await cog.shortcuts.tbc(inter, "Рейтинг самому себе повысить нельзя")
      )
      return
    if view.bot:
      await inter.edit_original_response(
        await cog.shortcuts.tbc(inter, "Рейтинг ботов нельзя повышать")
      )
      return

    ratings = await self.bot.database.readSocialRating(
      user_id=view.id
    )
    if not ratings:
      await self.bot.database.createSocialRating(view.id, 0)
      
      ratings = await self.bot.database.readSocialRating(
        user_id=view.id,
        cacheOverwrite=True
      )
    ratingRecord = ratings[0]

    newRating = ratingRecord.rating + 1
    
    await self.bot.database.updateSocialRating(
      user_id=view.id,
      to_rating=newRating
    )

    color = 0x1ED860 if newRating > 0 else 0xDF4E4E
    embed = cog.Embed(
      title=await cog.shortcuts.tbc(inter, f"Рейтинг {view.display_name} повышен"),
      description=f"## {ratingRecord.rating} => {newRating}",
      color=color,
    ).set_thumbnail(url=view.display_avatar.url)
    await inter.edit_original_response(embed=embed)

  @cooldown(1, 43200, BucketType.user)
  @rating.sub_command(
    name="remove",
    description=cog.Localised("Down someone's rating", key="rating_remove_desc"),
  )
  async def remove(
    self,
    inter: cog.ApplicationCommandInteraction,
    view: cog.Member = cog.Param(description="Чей рейтинг понижаем"),
  ):
    await inter.response.defer(ephemeral=True)

    blocked = {config.bot_owner_id} if config.bot_owner_id is not None else set()
    if view == inter.author or inter.author.id in blocked:
      await inter.edit_original_response(
        await cog.shortcuts.tbc(inter, "Вам запрещено взаимодействовать с рейтингами!")
      )
      return
    if view.bot:
      await inter.edit_original_response(
        await cog.shortcuts.tbc(inter, "Рейтинг ботов нельзя понижать")
      )
      return

    ratings = await self.bot.database.readSocialRating(
      user_id=view.id
    )
    if not ratings:
      await self.bot.database.createSocialRating(view.id, 0)
      
      ratings = await self.bot.database.readSocialRating(
        user_id=view.id,
        cacheOverwrite=True
      )
    ratingRecord = ratings[0]
    newRating = ratingRecord.rating - 1

    await self.bot.database.updateSocialRating(
      user_id=view.id,
      to_rating=newRating
    )

    color = 0x1ED860 if newRating > 0 else 0xDF4E4E
    embed = cog.Embed(
      title=await cog.shortcuts.tbc(inter, f"Рейтинг {view.display_name} понижен"),
      description=f"## {ratingRecord.rating} => {newRating}",
      color=color,
    ).set_thumbnail(url=view.display_avatar.url)

    await inter.edit_original_response(embed=embed)

def setup(bot: cog.MemeismBot):
  bot.add_cog(Rating(bot))
  bot.cog_reload(__name__)