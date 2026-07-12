import { redirect } from "next/navigation";
async function App() {
    return redirect(
        `https://discord.com/oauth2/authorize?client_id=${process.env.DISCORD_CLIENT_ID}&permissions=285280256824&scope=bot%20applications.commands&redirect_uri=${process.env.DISCORD_REDIRECT_URI}&integration_type=0&response_type=code`,
    );
}

export default App;
