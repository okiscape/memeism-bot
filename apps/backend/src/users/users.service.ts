import { Injectable } from "@nestjs/common";
import { PrismaService } from "../prisma/prisma.service";

@Injectable()
export class UsersService {
    constructor(private prisma: PrismaService) {}

    async getProfile(userId: string) {
        const profile = await this.prisma.userProfile.findUnique({
            where: { userId: BigInt(userId) },
        });
        return {
            aboutMe: profile?.aboutMe,
            color: profile?.color,
            image: profile?.customImage,
        };
    }

    async getSettings(userId: string) {
        const settings = await this.prisma.userSettings.findUnique({
            where: { userId: BigInt(userId) },
        });
        return {
            osuUsername: settings?.osuUsername,
            timezone: settings?.timezone,
        };
    }

    async getSocialRating(userId: string) {
        const rating = await this.prisma.socialRating.findUnique({
            where: { userId: BigInt(userId) },
        });
        return rating?.rating;
    }

    async getFullProfile(userId: string) {
        const [profile, settings, rating] = await Promise.all([
            this.getProfile(userId),
            this.getSettings(userId),
            this.getSocialRating(userId),
        ]);
        return { profile, settings, rating };
    }
}
