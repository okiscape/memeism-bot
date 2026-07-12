import {
    CanActivate,
    ExecutionContext,
    ForbiddenException,
    Injectable,
    UnauthorizedException,
} from "@nestjs/common";
import { AuthService } from "./auth.service";
import { Request } from "express";

@Injectable()
export class GuildAdminGuard implements CanActivate {
    constructor(private authService: AuthService) {}

    async canActivate(context: ExecutionContext): Promise<boolean> {
        const request = context.switchToHttp().getRequest<Request>();
        const token = request.cookies?.session_token;

        if (!token) {
            throw new UnauthorizedException("Not authenticated");
        }

        try {
            const user = await this.authService.getUser(token);
            request.discordUser = user;
        } catch {
            throw new UnauthorizedException("Invalid or expired token");
        }

        const guildId = Array.isArray(request.params.id)
            ? request.params.id[0]
            : request.params.id;
        if (!guildId) {
            throw new ForbiddenException("Guild ID is required");
        }

        const hasAccess = await this.authService.checkUserGuildAccess(
            token,
            guildId,
        );
        if (!hasAccess) {
            throw new ForbiddenException(
                "You don't have permission to manage this guild",
            );
        }

        return true;
    }
}
