export interface DiscordUser {
  id: string;
  username: string;
  discriminator: string;
  globalName: string | null;
  avatar: string | null;
}

export interface DiscordGuild {
  id: string;
  name: string;
  icon: string | null;
  owner: boolean;
  permissions: string;
}

export interface ServerSettings {
  guildId: string;
  averageLanguage: string | null;
  badWords: string | null;
  notifiedModerators: string | null;
  notifyChannel: string | null;
  badWordsAction: string | null;
  joinChannel: string | null;
  leaveChannel: string | null;
  postChannel: string | null;
  muteRole: string | null;
  autoRole: string | null;
  logChannel: string | null;
  verifiedRole: string | null;
  ticketCategory: string | null;
  fareText: string | null;
  fareColor: string | null;
  fareImage: string | null;
  greetText: string | null;
  greetColor: string | null;
  greetImage: string | null;
  privateCrChannel: string | null;
  privateCategory: string | null;
  customGreet: string | null;
  customFare: string | null;
  notifyText: string | null;
}

export interface UserProfile {
  userId: string;
  aboutMe: string | null;
  color: string | null;
  customImage: string | null;
}

export interface SocialRating {
  userId: string;
  rating: number;
}

export interface BotStatus {
  status: 'online' | 'offline' | 'starting';
  uptime: number;
  memory: {
    rss: number;
    heapTotal: number;
    heapUsed: number;
    external: number;
  };
}
