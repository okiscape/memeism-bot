import {
    Controller,
    Get,
    Param,
    UseGuards,
    Request as Req,
} from "@nestjs/common";
import { Request as ExpressRequest } from "express";
import { UsersService } from "./users.service";
import { AuthService } from "../auth/auth.service";
import { DiscordGuard } from "../auth/discord.guard";
import { CurrentUser } from "../auth/current-user.decorator";
import { DiscordUser } from "../auth/discord-user.interface";

@Controller("users")
export class UsersController {
    constructor(
        private usersService: UsersService,
        private authService: AuthService,
    ) {}

    @Get("@me/guilds")
    @UseGuards(DiscordGuard)
    async getMyGuilds(@CurrentUser() user: DiscordUser, @Req() req: ExpressRequest) {
        const token = req.cookies.session_token;
        return this.authService.getAllUserGuildsWithBotStatus(token);
    }

    @Get("@me/discord-profile")
    @UseGuards(DiscordGuard)
    async getMyDiscordProfile(@CurrentUser() user: DiscordUser) {
        return {
            id: user.id,
            username: user.username,
            global_name: user.global_name,
            avatar: user.avatar,
            banner: user.banner,
            accent_color: user.accent_color,
            avatar_decoration_data: user.avatar_decoration_data,
            collectibles: user.collectibles,
        };
    }

    @Get("@me/profile")
    @UseGuards(DiscordGuard)
    async getMyProfile(@CurrentUser() user: DiscordUser) {
        return this.usersService.getProfile(user.id);
    }

    @Get("@me/settings")
    @UseGuards(DiscordGuard)
    async getMySettings(@CurrentUser() user: DiscordUser) {
        return this.usersService.getSettings(user.id);
    }

    @Get("@me/rating")
    @UseGuards(DiscordGuard)
    async getMyRating(@CurrentUser() user: DiscordUser) {
        return this.usersService.getSocialRating(user.id);
    }

    @Get("@me")
    @UseGuards(DiscordGuard)
    async getMyFullProfile(@CurrentUser() user: DiscordUser) {
        return this.usersService.getFullProfile(user.id);
    }

    @Get(":id/profile")
    async getProfile(@Param("id") id: string) {
        return this.usersService.getProfile(id);
    }

    @Get(":id/settings")
    async getSettings(@Param("id") id: string) {
        return this.usersService.getSettings(id);
    }

    @Get(":id/rating")
    async getRating(@Param("id") id: string) {
        return this.usersService.getSocialRating(id);
    }

    @Get(":id")
    async getFullProfile(@Param("id") id: string) {
        return this.usersService.getFullProfile(id);
    }
}
