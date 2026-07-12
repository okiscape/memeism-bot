import { createParamDecorator, ExecutionContext } from "@nestjs/common";
import { DiscordUser } from "./discord-user.interface";

export const CurrentUser = createParamDecorator(
    (data: keyof DiscordUser | undefined, ctx: ExecutionContext) => {
        const request = ctx.switchToHttp().getRequest();
        const user: DiscordUser = request.discordUser;

        if (data) {
            return user[data];
        }

        return user;
    },
);
