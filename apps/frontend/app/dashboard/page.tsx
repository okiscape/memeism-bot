import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import "./page.css";
import ServersList from "./servers";

export default async function DashboardPage() {
    const cookieStore = await cookies();
    const sessionToken = cookieStore.get("session_token")?.value;

    if (!sessionToken) return redirect("/login");

    return (
        <div className="dashboard-container">
            <ServersList />
        </div>
    );
}
