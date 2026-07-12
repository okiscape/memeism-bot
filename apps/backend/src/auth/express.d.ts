import { DiscordUser } from "./discord-user.interface";

declare module "express" {
    interface Request {
        discordUser?: DiscordUser;
    }
}
