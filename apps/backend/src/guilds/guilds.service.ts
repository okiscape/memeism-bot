import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

const bigIntFields = [
  'notifyChannel', 'joinChannel', 'leaveChannel', 'postChannel',
  'muteRole', 'autoRole', 'logChannel', 'verifiedRole',
  'ticketCategory', 'privateCrChannel', 'privateCategory',
];

function serializeBigInts(obj: any): any {
  if (obj === null || obj === undefined) return obj;
  if (typeof obj === 'bigint') return obj.toString();
  if (Array.isArray(obj)) return obj.map(serializeBigInts);
  if (typeof obj === 'object') {
    const result: any = {};
    for (const [key, value] of Object.entries(obj)) {
      result[key] = serializeBigInts(value);
    }
    return result;
  }
  return obj;
}

@Injectable()
export class GuildsService {
  constructor(private prisma: PrismaService) {}

  async getSettings(guildId: string) {
    const settings = await this.prisma.serverSettings.findUnique({
      where: { guildId: BigInt(guildId) },
    });
    return serializeBigInts(settings);
  }

  async updateSettings(guildId: string, data: Record<string, unknown>) {
    const processed: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(data)) {
      if (bigIntFields.includes(key) && value !== null) {
        processed[key] = BigInt(value as string);
      } else {
        processed[key] = value;
      }
    }

    const result = await this.prisma.serverSettings.upsert({
      where: { guildId: BigInt(guildId) },
      create: { guildId: BigInt(guildId), ...processed },
      update: processed,
    });
    return serializeBigInts(result);
  }

  async deleteSettings(guildId: string) {
    return this.prisma.serverSettings.delete({
      where: { guildId: BigInt(guildId) },
    });
  }
}