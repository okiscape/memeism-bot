"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_BACKEND_URL;
const CLIENT_ID = process.env.NEXT_PUBLIC_DISCORD_CLIENT_ID;
const PERMISSIONS = process.env.NEXT_PUBLIC_BOT_PERMISSIONS;

interface UserProfile {
    id: string;
    username: string;
    global_name: string | null;
    avatar: string | null;
}

interface Guild {
    id: string;
    name: string;
    icon: string | null;
    owner: boolean;
    hasBot: boolean;
}

function avatarUrl(user: UserProfile): string {
    if (!user.avatar) {
        const idx = Number(BigInt(user.id) >> BigInt(22)) % 6;
        return `https://cdn.discordapp.com/embed/avatars/${idx}.png`;
    }
    const ext = user.avatar.startsWith("a_") ? "gif" : "png";
    return `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.${ext}`;
}

function guildIconUrl(icon: string, guildId: string): string {
    const ext = icon.startsWith("a_") ? "gif" : "png";
    return `https://cdn.discordapp.com/icons/${guildId}/${icon}.${ext}`;
}

function inviteUrl(guildId: string): string {
    return `https://discord.com/oauth2/authorize?client_id=${CLIENT_ID}&guild_id=${guildId}&permissions=${PERMISSIONS}&integration_type=0&response_type=code&scope=bot+applications.commands`;
}

function GuildCard({
    guild,
    onClick,
    onInvite,
}: {
    guild: Guild;
    onClick: () => void;
    onInvite?: () => void;
}) {
    const icon = guild.icon ? guildIconUrl(guild.icon, guild.id) : null;

    return (
        <div className="servers-card">
            <button className="servers-card-body" onClick={onClick}>
                {icon ? (
                    <img
                        className="servers-card-icon"
                        src={icon}
                        alt={guild.name}
                    />
                ) : (
                    <div className="servers-card-icon servers-card-icon--fallback">
                        {guild.name
                            .split(" ")
                            .map((w) => w[0])
                            .join("")
                            .slice(0, 2)
                            .toUpperCase()}
                    </div>
                )}
                <span className="servers-card-name">{guild.name}</span>
            </button>
            {onInvite && (
                <div className="servers-card-invite-container">
                    <a
                        className="servers-card-invite"
                        href={inviteUrl(guild.id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                    >
                        Add Bot
                    </a>
                </div>
            )}
        </div>
    );
}

export default function ServersList() {
    const router = useRouter();
    const [user, setUser] = useState<UserProfile | null>(null);
    const [guilds, setGuilds] = useState<Guild[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            fetch(`${API}/api/auth/me`, { credentials: "include" }),
            fetch(`${API}/api/users/@me/guilds`, { credentials: "include" }),
        ])
            .then(async ([meRes, guildsRes]) => {
                if (!meRes.ok) {
                    window.location.href = "/";
                    return;
                }
                const me = await meRes.json();
                const g = guildsRes.ok ? await guildsRes.json() : [];
                setUser(me);
                setGuilds(g);
            })
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return <div className="dashboard-status">Loading...</div>;
    }

    if (!user) return null;

    const withBot = guilds.filter((g) => g.hasBot);
    const withoutBot = guilds.filter((g) => !g.hasBot);

    return (
        <div className="servers-page">
            <div className="servers-user">
                <img
                    className="servers-avatar"
                    src={avatarUrl(user)}
                    alt={user.username}
                />
                <span className="servers-username">
                    Welcome to the Kisa Dashboard,{" "}
                    {user.global_name || user.username}!
                </span>
            </div>

            {withBot.length > 0 && (
                <>
                    <h2 className="servers-heading">Controllable Servers</h2>
                    <div className="servers-grid">
                        {withBot.map((guild) => (
                            <GuildCard
                                key={guild.id}
                                guild={guild}
                                onClick={() =>
                                    router.push(`/dashboard/${guild.id}`)
                                }
                            />
                        ))}
                    </div>
                </>
            )}

            {withoutBot.length > 0 && (
                <>
                    <h2 className="servers-heading">Add Bot to Server</h2>
                    <div className="servers-grid">
                        {withoutBot.map((guild) => (
                            <GuildCard
                                key={guild.id}
                                guild={guild}
                                onClick={() => {}}
                                onInvite={() => {}}
                            />
                        ))}
                    </div>
                </>
            )}

            {guilds.length === 0 && (
                <p className="servers-empty">
                    No servers found where you have admin access.
                </p>
            )}
        </div>
    );
}
