import {
    CanActivate,
    ExecutionContext,
    Injectable,
    UnauthorizedException,
} from "@nestjs/common";
import { AuthService } from "./auth.service";
import { Request } from "express";

@Injectable()
export class DiscordGuard implements CanActivate {
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
            return true;
        } catch {
            throw new UnauthorizedException("Invalid or expired token");
        }
    }
}
