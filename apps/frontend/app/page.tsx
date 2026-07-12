import { cookies } from "next/headers";

import "./page.css";
import { Link } from "next-view-transitions";

const FEATURES = [
    "Social rating",
    "Profile customization",
    "Games integrations",
    "Servers linking",
    "Server statistics",
    "Leveling",
    "Open Source",
    "Temporary Chats",
    "Moderation",
    "And many more!",
];

const ROW_HEIGHT = 58;
const SECONDS_PER_ROW = 3;

async function App() {
    const doubled = [...FEATURES, ...FEATURES];
    const totalHeight = FEATURES.length * ROW_HEIGHT;
    const duration = FEATURES.length * SECONDS_PER_ROW;

    const cookieStore = await cookies();
    const sessionToken = cookieStore.get("session_token")?.value;
    const isLoggedIn = Boolean(sessionToken);

    return (
        <div className="hero-sect">
            <div className="infopad">
                <h1>
                    <i>Kisa</i>
                </h1>
                <p>All-in-one discord bot</p>
                <div className="kisacontainer">
                    {isLoggedIn ? (
                        <Link className="kisabutton" href="/dashboard">
                            Dashboard
                        </Link>
                    ) : (
                        <a className="kisabutton warm" href="/login">
                            Add to Discord
                        </a>
                    )}
                </div>
            </div>
            <div className="featurerain">
                <div
                    className="featurerain-track"
                    style={{
                        "--scroll-distance": `${totalHeight}px`,
                        "--scroll-duration": `${duration}s`,
                    } as React.CSSProperties}
                >
                    {doubled.map((text, i) => {
                        const isLeft = i % 2 === 0;
                        return (
                            <div className="featurerain-row" key={i}>
                                <div
                                    className="featurerain-half"
                                    style={{
                                        justifyContent: isLeft
                                            ? "flex-end"
                                            : "flex-start",
                                        marginLeft: isLeft ? "0" : "50%",
                                    }}
                                >
                                    <span className="featurerain-pill">
                                        {text}
                                    </span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}

export default App;
