import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import GuildSettings from "./guild-settings";
import "./page.css";

export default async function GuildPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const cookieStore = await cookies();
    const sessionToken = cookieStore.get("session_token")?.value;
    if (!sessionToken) return redirect("/login");

    const { id } = await params;

    return (
        <div className="guild-page">
            <GuildSettings guildId={id} />
        </div>
    );
}
