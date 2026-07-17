"use client";

import { Link } from "next-view-transitions";
import { useEffect, useState, useCallback } from "react";

const API = process.env.NEXT_PUBLIC_BACKEND_URL;

interface ServerSettings {
    guildId: string;
    averageLanguage: string | null;
    badWords: string | null;
    badWordsAction: string | null;
    notifiedModerators: string | null;
    notifyChannel: string | null;
    notifyText: string | null;
    joinChannel: string | null;
    leaveChannel: string | null;
    postChannel: string | null;
    greetText: string | null;
    greetColor: string | null;
    greetImage: string | null;
    customGreet: string | null;
    fareText: string | null;
    fareColor: string | null;
    fareImage: string | null;
    customFare: string | null;
    muteRole: string | null;
    autoRole: string | null;
    logChannel: string | null;
    verifiedRole: string | null;
    ticketCategory: string | null;
    privateCrChannel: string | null;
    privateCategory: string | null;
}

type FieldKey = keyof Omit<ServerSettings, "guildId">;

interface FieldDef {
    key: FieldKey;
    label: string;
    placeholder?: string;
    type?: "text" | "textarea";
}

interface Category {
    id: string;
    label: string;
    fields: FieldDef[];
}

const CATEGORIES: Category[] = [
    {
        id: "greeting",
        label: "Greeting",
        fields: [
            {
                key: "greetText",
                label: "Greet Text",
                placeholder: "Welcome to the server!",
                type: "textarea",
            },
            { key: "greetColor", label: "Greet Color", placeholder: "#ff9e3d" },
            {
                key: "greetImage",
                label: "Greet Image URL",
                placeholder: "https://...",
            },
            { key: "customGreet", label: "Custom Greet", type: "textarea" },
        ],
    },
    {
        id: "farewell",
        label: "Farewell",
        fields: [
            {
                key: "fareText",
                label: "Farewell Text",
                placeholder: "Goodbye!",
                type: "textarea",
            },
            {
                key: "fareColor",
                label: "Farewell Color",
                placeholder: "#ff9e3d",
            },
            {
                key: "fareImage",
                label: "Farewell Image URL",
                placeholder: "https://...",
            },
            { key: "customFare", label: "Custom Farewell", type: "textarea" },
        ],
    },
    {
        id: "moderation",
        label: "Moderation",
        fields: [
            {
                key: "badWords",
                label: "Bad Words (comma-separated)",
                placeholder: "word1, word2, ...",
            },
            {
                key: "badWordsAction",
                label: "Bad Words Action",
                placeholder: "delete / mute / warn",
            },
            {
                key: "muteRole",
                label: "Mute Role ID",
                placeholder: "1234567890",
            },
            {
                key: "verifiedRole",
                label: "Verified Role ID",
                placeholder: "1234567890",
            },
            {
                key: "notifiedModerators",
                label: "Notified Moderators",
                placeholder: "1234567890",
            },
        ],
    },
    {
        id: "roles",
        label: "Roles",
        fields: [
            {
                key: "autoRole",
                label: "Auto Role ID",
                placeholder: "1234567890",
            },
            {
                key: "muteRole",
                label: "Mute Role ID",
                placeholder: "1234567890",
            },
            {
                key: "verifiedRole",
                label: "Verified Role ID",
                placeholder: "1234567890",
            },
        ],
    },
    {
        id: "channels",
        label: "Channels",
        fields: [
            {
                key: "joinChannel",
                label: "Join Channel ID",
                placeholder: "1234567890",
            },
            {
                key: "leaveChannel",
                label: "Leave Channel ID",
                placeholder: "1234567890",
            },
            {
                key: "logChannel",
                label: "Log Channel ID",
                placeholder: "1234567890",
            },
            {
                key: "notifyChannel",
                label: "Notify Channel ID",
                placeholder: "1234567890",
            },
            {
                key: "postChannel",
                label: "Post Channel ID",
                placeholder: "1234567890",
            },
            {
                key: "ticketCategory",
                label: "Ticket Category ID",
                placeholder: "1234567890",
            },
            {
                key: "privateCrChannel",
                label: "Private Cr Channel ID",
                placeholder: "1234567890",
            },
            {
                key: "privateCategory",
                label: "Private Category ID",
                placeholder: "1234567890",
            },
        ],
    },
    {
        id: "language",
        label: "Language",
        fields: [
            {
                key: "averageLanguage",
                label: "Server Language",
                placeholder: "en / ru",
            },
        ],
    },
];

const EMPTY_SETTINGS: ServerSettings = {
    guildId: "",
    averageLanguage: null,
    badWords: null,
    badWordsAction: null,
    notifiedModerators: null,
    notifyChannel: null,
    notifyText: null,
    joinChannel: null,
    leaveChannel: null,
    postChannel: null,
    greetText: null,
    greetColor: null,
    greetImage: null,
    customGreet: null,
    fareText: null,
    fareColor: null,
    fareImage: null,
    customFare: null,
    muteRole: null,
    autoRole: null,
    logChannel: null,
    verifiedRole: null,
    ticketCategory: null,
    privateCrChannel: null,
    privateCategory: null,
};

function buildInitialState(data: Record<string, any>): ServerSettings {
    const state = { ...EMPTY_SETTINGS };
    for (const key of Object.keys(state) as (keyof ServerSettings)[]) {
        if (key in data && data[key] !== null && data[key] !== undefined) {
            (state as any)[key] = String(data[key]);
        }
    }
    return state;
}

function FieldInput({
    field,
    value,
    onChange,
}: {
    field: FieldDef;
    value: string;
    onChange: (val: string) => void;
}) {
    if (field.type === "textarea") {
        return (
            <label className="guild-field">
                <span className="guild-label">{field.label}</span>
                <textarea
                    className="guild-input"
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder={field.placeholder}
                    rows={3}
                />
            </label>
        );
    }
    return (
        <label className="guild-field">
            <span className="guild-label">{field.label}</span>
            <input
                className="guild-input"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={field.placeholder}
            />
        </label>
    );
}

interface GuildInfo {
    id: string;
    name: string;
    icon: string | null;
}

function GuildPreview({ guild }: { guild: GuildInfo | null }) {
    if (!guild) return null;

    let iconSrc: string | null = null;
    if (guild.icon) {
        const ext = guild.icon.startsWith("a_") ? "gif" : "png";
        iconSrc = `https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.${ext}`;
    }

    return (
        <div className="guild-preview">
            {iconSrc ? (
                <img
                    className="guild-preview-icon"
                    src={iconSrc}
                    alt={guild.name}
                />
            ) : (
                <div className="guild-preview-icon guild-preview-icon--fallback">
                    {guild.name
                        .split(" ")
                        .map((w) => w[0])
                        .join("")
                        .slice(0, 2)
                        .toUpperCase()}
                </div>
            )}
            <span className="guild-preview-name">{guild.name}</span>
        </div>
    );
}

export default function GuildSettings({ guildId }: { guildId: string }) {
    const [settings, setSettings] = useState<ServerSettings>(EMPTY_SETTINGS);
    const [guild, setGuild] = useState<GuildInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [status, setStatus] = useState<"idle" | "ok" | "error">("idle");
    const [activeTab, setActiveTab] = useState(CATEGORIES[0].id);

    useEffect(() => {
        Promise.all([
            fetch(`${API}/api/guilds/${guildId}`, { credentials: "include" }),
            fetch(`${API}/api/guilds/${guildId}/settings`, {
                credentials: "include",
            }),
        ])
            .then(async ([guildRes, settingsRes]) => {
                if (guildRes.ok) {
                    setGuild(await guildRes.json());
                }
                if (settingsRes.ok) {
                    const data = await settingsRes.json();
                    if (data) setSettings(buildInitialState(data));
                }
            })
            .finally(() => setLoading(false));
    }, [guildId]);

    const update = useCallback((field: FieldKey, value: string) => {
        setSettings((prev) => ({ ...prev, [field]: value || null }));
        setStatus("idle");
    }, []);

    const handleSave = async () => {
        setSaving(true);
        setStatus("idle");
        try {
            const res = await fetch(`${API}/api/guilds/${guildId}/settings`, {
                method: "PUT",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(settings),
            });
            if (res.ok) {
                const data = await res.json();
                setSettings(buildInitialState(data));
                setStatus("ok");
            } else {
                setStatus("error");
            }
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="guild-status">
                <div className="loading-container">
                    <div className="bar" />
                </div>{" "}
                Loading settings...
            </div>
        );
    }

    const activeCategory = CATEGORIES.find((c) => c.id === activeTab)!;

    return (
        <div className="guild-layout">
            <nav className="guild-sidebar">
                <Link href="/dashboard" className="back">
                    &lt;- Back
                </Link>
                <GuildPreview guild={guild} />
                {CATEGORIES.map((cat) => (
                    <button
                        key={cat.id}
                        className={`guild-nav-item ${activeTab === cat.id ? "guild-nav-item--active" : ""}`}
                        onClick={() => setActiveTab(cat.id)}
                    >
                        {cat.label}
                    </button>
                ))}
            </nav>

            <div className="guild-content">
                <div className="guild-content-header">
                    <h1 className="guild-title">{activeCategory.label}</h1>
                </div>

                <div className="guild-fields">
                    {activeCategory.fields.map((field) => (
                        <FieldInput
                            key={field.key}
                            field={field}
                            value={(settings[field.key] as string) ?? ""}
                            onChange={(val) => update(field.key, val)}
                        />
                    ))}
                </div>

                <div className="guild-actions">
                    <button
                        className="guild-save-btn"
                        onClick={handleSave}
                        disabled={saving}
                    >
                        {saving ? "Saving..." : "Save"}
                    </button>
                    {status === "ok" && (
                        <span className="guild-status-msg guild-status-msg--ok">
                            Saved
                        </span>
                    )}
                    {status === "error" && (
                        <span className="guild-status-msg guild-status-msg--error">
                            Error
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}
