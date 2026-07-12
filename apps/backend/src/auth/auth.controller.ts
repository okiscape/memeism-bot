import { Controller, Get, Query, Res, HttpStatus, UseGuards } from "@nestjs/common";
import { Response } from "express";
import { ConfigService } from "@nestjs/config";
import { AuthService } from "./auth.service";
import { DiscordGuard } from "./discord.guard";
import { CurrentUser } from "./current-user.decorator";
import { DiscordUser } from "./discord-user.interface";

@Controller("auth")
export class AuthController {
    constructor(
        private authService: AuthService,
        private config: ConfigService,
    ) {}

    @Get("discord")
    discordAuth(@Res() res: Response) {
        const clientId = this.config.getOrThrow("DISCORD_CLIENT_ID");
        const redirectUri = this.config.getOrThrow("DISCORD_REDIRECT_URI");
        const url = `https://discord.com/api/oauth2/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri!)}&response_type=code&scope=identify+guilds`;
        res.redirect(url);
    }

    @Get("callback/discord")
    async callback(@Query("code") code: string, @Res() res: Response) {
        try {
            if (!code) {
                return res
                    .status(HttpStatus.BAD_REQUEST)
                    .json({ error: "No code provided" });
            }

            const tokenData = await this.authService.exchangeCode(code);

            const frontendUrl = this.config.getOrThrow("FRONTEND_URL");
            const dashboardUrl = `${frontendUrl}/dashboard`;

            res.cookie("session_token", tokenData.access_token, {
                httpOnly: true,
                secure: process.env.NODE_ENV === "production",
                sameSite: "lax",
                maxAge: 1000 * 60 * 60 * 24 * 7,
                path: "/",
            });

            return res.redirect(dashboardUrl);
        } catch (error) {
            const frontendUrl = this.config.getOrThrow("FRONTEND_URL");
            return res.redirect(`${frontendUrl}/login?error=auth_failed`);
        }
    }

    @Get("me")
    @UseGuards(DiscordGuard)
    getMe(@CurrentUser() user: DiscordUser) {
        return {
            id: user.id,
            username: user.username,
            global_name: user.global_name,
            avatar: user.avatar,
            banner: user.banner,
            accent_color: user.accent_color,
        };
    }

    @Get("logout")
    logout(@Res() res: Response) {
        res.clearCookie("session_token", { path: "/" });
        return res.json({ ok: true });
    }
}
