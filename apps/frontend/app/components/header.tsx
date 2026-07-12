import { Link } from "next-view-transitions";
import "./header.css";

export default function App() {
    return (
        <div className="header-container">
            <div className="header-section items-start">
                <Link className="title" href="/">
                    Kisa
                </Link>
            </div>
            <div className="header-section">
                <Link className="dashboard" href="/dashboard">
                    Dashboard
                </Link>
            </div>
        </div>
    );
}
