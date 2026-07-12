import {
    Controller,
    Get,
    Put,
    Delete,
    Param,
    Body,
    UseGuards,
} from "@nestjs/common";
import { GuildsService } from "./guilds.service";
import { AuthService } from "../auth/auth.service";
import { GuildAdminGuard } from "../auth/guild-admin.guard";
import { CurrentUser } from "../auth/current-user.decorator";
import { DiscordUser } from "../auth/discord-user.interface";

@Controller("guilds")
export class GuildsController {
    constructor(
        private guildsService: GuildsService,
        private authService: AuthService,
    ) {}

    @Get(":id")
    @UseGuards(GuildAdminGuard)
    async getGuild(
        @Param("id") id: string,
        @CurrentUser() user: DiscordUser,
    ) {
        return this.authService.getGuildInfo(id);
    }

    @Get(":id/settings")
    @UseGuards(GuildAdminGuard)
    async getSettings(
        @Param("id") id: string,
        @CurrentUser() user: DiscordUser,
    ) {
        return this.guildsService.getSettings(id);
    }

    @Put(":id/settings")
    @UseGuards(GuildAdminGuard)
    async updateSettings(
        @Param("id") id: string,
        @Body() body: Record<string, unknown>,
        @CurrentUser() user: DiscordUser,
    ) {
        return this.guildsService.updateSettings(id, body);
    }

    @Delete(":id/settings")
    @UseGuards(GuildAdminGuard)
    async deleteSettings(
        @Param("id") id: string,
        @CurrentUser() user: DiscordUser,
    ) {
        return this.guildsService.deleteSettings(id);
    }

    @Get(":id/roles")
    @UseGuards(GuildAdminGuard)
    async getRoles(
        @Param("id") id: string,
        @CurrentUser() user: DiscordUser,
    ) {
        return this.authService.getGuildRoles(id);
    }
}
