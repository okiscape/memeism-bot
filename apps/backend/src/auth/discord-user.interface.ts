export interface DiscordUser {
    id: string;
    username: string;
    global_name: string | null;
    avatar: string | null;
    banner: string | null;
    accent_color: number | null;
    avatar_decoration_data: {
        asset: string;
        sku_id: string;
        expires_at: number | null;
    } | null;
    collectibles: {
        nameplate: {
            sku_id: string;
            asset: string;
            label: string;
            palette: string;
        } | null;
    } | null;
}
