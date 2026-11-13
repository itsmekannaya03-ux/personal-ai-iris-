"""
IRIS / Iris AI - Website Builder & Dynamic Webpage Generator
Generates production-grade, responsive modern websites based on user commands and opens them in the browser.
"""

import os
import re
import sys
import logging
import webbrowser
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger("iris.hands.website_builder")


class WebsiteBuilder:
    """
    Creates responsive, modern, multi-section websites
    and opens them immediately in the user's browser.
    """

    def __init__(self, file_ops=None, generator_fn: Optional[Callable[[str], str]] = None):
        self._file_ops = file_ops
        self._generator_fn = generator_fn

    def resolve_destination(self, description: str = "", target_dir: Optional[str] = None) -> Path:
        """Resolve destination without creating unnecessary subfolders."""
        if target_dir:
            p = Path(target_dir).expanduser()
            if p.exists():
                return p

        d = description.lower()
        user_home = Path.home()
        desktop = user_home / "OneDrive" / "Desktop"
        if not desktop.exists():
            desktop = user_home / "Desktop"

        if self._file_ops and hasattr(self._file_ops, "get_working_dir"):
            wd = self._file_ops.get_working_dir()
            if wd and any(w in d for w in ("project", "work", "here", "workspace", "this folder")):
                return Path(wd)

        if "download" in d:
            return user_home / "Downloads"
        if "document" in d:
            docs = user_home / "OneDrive" / "Documents"
            return docs if docs.exists() else (user_home / "Documents")

        return desktop

    def create_and_open(self, topic: str, description: str = "", target_dir: Optional[str] = None) -> dict:
        """Build website HTML and launch it immediately in the browser."""
        dest_dir = self.resolve_destination(description, target_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        clean_topic = topic.strip()
        slug = re.sub(r"[^a-z0-9]+", "_", clean_topic.lower()).strip("_") or "modern"
        filename = f"{slug}_website.html"

        html_content = self._generate_website_code(clean_topic, description)
        out_path = dest_dir / filename

        try:
            out_path.write_text(html_content, encoding="utf-8")
            logger.info(f"Saved website to: {out_path}")
        except Exception as e:
            return {"success": False, "error": f"Failed to save website: {e}"}

        try:
            webbrowser.open(out_path.resolve().as_uri())
            return {
                "success": True,
                "path": str(out_path),
                "name": clean_topic,
                "message": f"Created modern website for '{clean_topic}' at {out_path} and opened it in your browser!",
            }
        except Exception as launch_err:
            return {
                "success": True,
                "path": str(out_path),
                "name": clean_topic,
                "message": f"Created website for '{clean_topic}' at {out_path}.",
            }

    def _generate_website_code(self, topic: str, description: str) -> str:
        """Generate high-aesthetic responsive HTML/CSS/JS website code."""
        d = (topic + " " + description).lower()

        # Check LLM generation first
        if self._generator_fn:
            try:
                prompt = (
                    f"Create a stunning, fully responsive, complete single-file modern website for: '{topic}'.\n"
                    f"Details from user: '{description}'.\n"
                    "Requirements:\n"
                    "- Complete HTML5 with embedded CSS and JavaScript.\n"
                    "- Modern aesthetics: Sleek dark theme with vibrant accents, glassmorphism, responsive flex/grid.\n"
                    "- Header with navigation, Hero section with CTA button, Features/Services section, Testimonials/Portfolio cards, Interactive Contact Form, Footer.\n"
                    "- Working interactive elements (theme toggle, smooth scrolling, modal or responsive drawer).\n"
                    "- Output ONLY the HTML document, no markdown code fences, no extra text."
                )
                generated = self._generator_fn(prompt)
                clean_html = re.sub(r"^```(?:html)?\s*", "", generated.strip(), flags=re.I)
                clean_html = re.sub(r"\s*```$", "", clean_html.strip())
                if "<!DOCTYPE html>" in clean_html or "<html" in clean_html:
                    return clean_html
            except Exception as ge:
                logger.warning(f"LLM website generation failed: {ge}")

        # High-aesthetic responsive modern templates
        if any(w in d for w in ("gym", "fitness", "workout", "trainer")):
            return self._gym_template(topic)
        if any(w in d for w in ("portfolio", "resume", "developer", "designer", "personal")):
            return self._portfolio_template(topic)
        if any(w in d for w in ("coffee", "cafe", "restaurant", "food", "bakery")):
            return self._restaurant_template(topic)

        return self._business_template(topic)

    def _portfolio_template(self, title: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | Portfolio</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; scroll-behavior: smooth; }}
  body {{ background: #090d16; color: #f1f5f9; font-family: 'Segoe UI', system-ui, sans-serif; line-height: 1.6; }}
  header {{ position: fixed; top: 0; left: 0; right: 0; display: flex; justify-content: space-between; align-items: center; padding: 20px 48px; background: rgba(9, 13, 22, 0.85); backdrop-filter: blur(16px); z-index: 100; border-bottom: 1px solid rgba(255,255,255,0.06); }}
  .logo {{ font-size: 1.4rem; font-weight: 800; background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
  nav a {{ color: #94a3b8; text-decoration: none; margin-left: 28px; font-weight: 500; transition: color 0.2s; }}
  nav a:hover {{ color: #38bdf8; }}
  .hero {{ min-height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: flex-start; padding: 0 48px; max-width: 1200px; margin: 0 auto; }}
  .badge {{ background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); padding: 6px 16px; border-radius: 9999px; font-size: 0.85rem; font-weight: 600; margin-bottom: 20px; }}
  h1 {{ font-size: 3.8rem; font-weight: 800; line-height: 1.1; margin-bottom: 20px; }}
  .highlight {{ background: linear-gradient(135deg, #38bdf8, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
  p.lead {{ font-size: 1.25rem; color: #94a3b8; max-width: 600px; margin-bottom: 32px; }}
  .cta-group {{ display: flex; gap: 16px; }}
  .btn-primary {{ background: linear-gradient(135deg, #0284c7, #6366f1); color: white; padding: 14px 32px; border-radius: 10px; font-weight: 600; text-decoration: none; border: none; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 8px 24px rgba(99,102,241,0.35); }}
  .btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 12px 30px rgba(99,102,241,0.5); }}
  .btn-secondary {{ background: rgba(255,255,255,0.06); color: #e2e8f0; padding: 14px 32px; border-radius: 10px; font-weight: 600; text-decoration: none; border: 1px solid rgba(255,255,255,0.12); transition: background 0.2s; }}
  .btn-secondary:hover {{ background: rgba(255,255,255,0.12); }}
  section {{ padding: 100px 48px; max-width: 1200px; margin: 0 auto; }}
  h2 {{ font-size: 2.4rem; font-weight: 700; margin-bottom: 40px; text-align: center; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; }}
  .card {{ background: rgba(30, 41, 59, 0.45); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 32px; backdrop-filter: blur(10px); transition: transform 0.2s, border-color 0.2s; }}
  .card:hover {{ transform: translateY(-4px); border-color: rgba(56, 189, 248, 0.4); }}
  .card h3 {{ font-size: 1.3rem; margin-bottom: 12px; color: #f8fafc; }}
  .card p {{ color: #94a3b8; font-size: 0.95rem; }}
  footer {{ text-align: center; padding: 40px; border-top: 1px solid rgba(255,255,255,0.06); color: #64748b; font-size: 0.9rem; }}
</style>
</head>
<body>
<header>
  <div class="logo">✦ {title}</div>
  <nav>
    <a href="#about">About</a>
    <a href="#work">Projects</a>
    <a href="#contact">Contact</a>
  </nav>
</header>
<main>
  <div class="hero">
    <div class="badge">Designed & Built by Iris AI</div>
    <h1>Innovating with <span class="highlight">Creativity & Code</span></h1>
    <p class="lead">Building state-of-the-art interactive digital experiences, clean systems architectures, and modern web applications.</p>
    <div class="cta-group">
      <a href="#work" class="btn-primary">View Projects</a>
      <a href="#contact" class="btn-secondary">Get In Touch</a>
    </div>
  </div>

  <section id="work">
    <h2>Featured Work</h2>
    <div class="grid">
      <div class="card">
        <h3>AI Agent Workspace</h3>
        <p>Next-generation autonomous system interface with multimodal vision and natural conversational engine.</p>
      </div>
      <div class="card">
        <h3>Cloud Architecture Suite</h3>
        <p>Ultra-low latency microservices streaming real-time analytics with resilient offline fallbacks.</p>
      </div>
      <div class="card">
        <h3>Interactive Canvas Engine</h3>
        <p>Zero-dependency 60fps game physics and rich interactive data visualizations built in vanilla JS.</p>
      </div>
    </div>
  </section>

  <section id="contact" style="text-align: center;">
    <h2>Let's Collaborate</h2>
    <p style="color: #94a3b8; margin-bottom: 30px;">Have an idea or project in mind? Let's connect and build something extraordinary.</p>
    <button class="btn-primary" onclick="alert('Thank you for reaching out! Iris has registered your interest.')">Send Message</button>
  </section>
</main>
<footer>
  <p>© 2026 {title} • Generated with excellence by Iris AI</p>
</footer>
</body>
</html>"""

    def _gym_template(self, title: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | Elite Fitness & Training</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0f1016; color: #f8fafc; font-family: 'Segoe UI', system-ui, sans-serif; }}
  header {{ display: flex; justify-content: space-between; align-items: center; padding: 24px 48px; border-bottom: 1px solid rgba(255,255,255,0.08); }}
  .logo {{ font-size: 1.5rem; font-weight: 900; color: #ef4444; text-transform: uppercase; letter-spacing: 2px; }}
  .hero {{ padding: 120px 48px; text-align: center; max-width: 900px; margin: 0 auto; }}
  h1 {{ font-size: 4rem; font-weight: 900; line-height: 1.1; margin-bottom: 24px; text-transform: uppercase; }}
  .accent {{ color: #ef4444; text-shadow: 0 0 30px rgba(239,68,68,0.5); }}
  p.lead {{ font-size: 1.25rem; color: #a1a1aa; margin-bottom: 36px; }}
  .btn {{ background: #ef4444; color: white; padding: 16px 40px; border-radius: 8px; font-weight: 800; font-size: 1rem; border: none; cursor: pointer; text-transform: uppercase; letter-spacing: 1px; box-shadow: 0 10px 25px rgba(239,68,68,0.4); }}
  .btn:hover {{ transform: scale(1.03); }}
  .programs {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; padding: 60px 48px; max-width: 1200px; margin: 0 auto; }}
  .card {{ background: #181922; border: 1px solid rgba(255,255,255,0.06); padding: 32px; border-radius: 12px; }}
  .card h3 {{ font-size: 1.4rem; color: #f43f5e; margin-bottom: 12px; }}
  .card p {{ color: #9ca3af; }}
  footer {{ text-align: center; padding: 40px; color: #71717a; border-top: 1px solid rgba(255,255,255,0.06); }}
</style>
</head>
<body>
<header>
  <div class="logo">⚡ {title}</div>
  <button class="btn" style="padding: 10px 24px; font-size: 0.85rem;" onclick="alert('Welcome to your free VIP pass!')">Free Trial</button>
</header>
<div class="hero">
  <h1>Unleash Your <span class="accent">Peak Potential</span></h1>
  <p class="lead">State of the art training facilities, expert athletic coaches, and customized high-intensity fitness programs.</p>
  <button class="btn" onclick="alert('Registration opened! A trainer will contact you shortly.')">Join Today</button>
</div>
<div class="programs">
  <div class="card">
    <h3>Strength & Conditioning</h3>
    <p>Build raw power and lean muscle with Olympic lifting platforms and heavy progressive resistance.</p>
  </div>
  <div class="card">
    <h3>HIIT & Combat Cardio</h3>
    <p>Ignite metabolism, increase endurance, and build explosive agility with functional combat circuits.</p>
  </div>
  <div class="card">
    <h3>Personal Coaching</h3>
    <p>1-on-1 personalized biomechanical coaching and precision nutrition planning for fast, lasting results.</p>
  </div>
</div>
<footer>
  <p>© 2026 {title} • Designed with Iris AI</p>
</footer>
</body>
</html>"""

    def _restaurant_template(self, title: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | Artisan Dining</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #12100e; color: #f5f5f4; font-family: 'Georgia', serif; line-height: 1.6; }}
  header {{ display: flex; justify-content: space-between; align-items: center; padding: 28px 48px; border-bottom: 1px solid rgba(217,119,6,0.2); }}
  .logo {{ font-size: 1.6rem; font-weight: 700; color: #f59e0b; letter-spacing: 1px; }}
  .hero {{ padding: 120px 48px; text-align: center; max-width: 800px; margin: 0 auto; }}
  h1 {{ font-size: 3.8rem; color: #fef3c7; margin-bottom: 20px; font-weight: 400; }}
  p.lead {{ font-size: 1.2rem; color: #d6d3d1; margin-bottom: 32px; font-family: sans-serif; }}
  .btn {{ background: #f59e0b; color: #1c1917; padding: 14px 36px; border: none; border-radius: 6px; font-weight: 700; font-family: sans-serif; cursor: pointer; }}
  .btn:hover {{ background: #d97706; }}
  .menu-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; padding: 40px 48px; max-width: 1100px; margin: 0 auto; }}
  .item {{ background: #1c1917; border: 1px solid rgba(217,119,6,0.15); padding: 24px; border-radius: 8px; font-family: sans-serif; }}
  .item h3 {{ color: #fef3c7; margin-bottom: 8px; font-family: serif; font-size: 1.3rem; display: flex; justify-content: space-between; }}
  .price {{ color: #f59e0b; font-weight: 700; }}
  footer {{ text-align: center; padding: 40px; color: #78716c; font-family: sans-serif; font-size: 0.85rem; border-top: 1px solid rgba(255,255,255,0.06); }}
</style>
</head>
<body>
<header>
  <div class="logo">🌿 {title}</div>
  <button class="btn" onclick="alert('Table reservation requested!')">Reserve Table</button>
</header>
<div class="hero">
  <h1>Artisan Flavors & Culinary Mastery</h1>
  <p class="lead">Farm-to-table organic ingredients handcrafted into seasonal delicacies with timeless passion.</p>
  <button class="btn" onclick="alert('Menu opened!')">Explore Full Menu</button>
</div>
<div class="menu-grid">
  <div class="item">
    <h3>Truffle Wild Mushroom Risotto <span class="price">$28</span></h3>
    <p style="color: #a8a29e;">Aged arborio rice simmered with forest chanterelles, white truffle oil, and Parmigiano-Reggiano.</p>
  </div>
  <div class="item">
    <h3>Herb-Crusted Sea Bass <span class="price">$36</span></h3>
    <p style="color: #a8a29e;">Pan-seared Mediterranean sea bass accompanied by saffron velouté and charred asparagus.</p>
  </div>
  <div class="item">
    <h3>Dark Chocolate Lava Soufflé <span class="price">$16</span></h3>
    <p style="color: #a8a29e;">Warm molten 70% Single-Origin Ecuadorian dark chocolate paired with Tahitian vanilla bean gelato.</p>
  </div>
</div>
<footer>
  <p>© 2026 {title} • Designed with Iris AI</p>
</footer>
</body>
</html>"""

    def _business_template(self, title: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | Modern Solutions</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; scroll-behavior: smooth; }}
  body {{ background: #0b0f19; color: #f8fafc; font-family: 'Segoe UI', system-ui, sans-serif; line-height: 1.6; }}
  header {{ display: flex; justify-content: space-between; align-items: center; padding: 20px 48px; background: rgba(11,15,25,0.8); backdrop-filter: blur(16px); position: fixed; top: 0; left: 0; right: 0; border-bottom: 1px solid rgba(255,255,255,0.06); z-index: 10; }}
  .logo {{ font-size: 1.4rem; font-weight: 700; color: #38bdf8; }}
  .hero {{ padding: 160px 48px 100px; text-align: center; max-width: 900px; margin: 0 auto; }}
  h1 {{ font-size: 3.6rem; font-weight: 800; line-height: 1.15; margin-bottom: 24px; }}
  .gradient {{ background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
  p.lead {{ font-size: 1.25rem; color: #94a3b8; margin-bottom: 36px; }}
  .btn {{ background: #2563eb; color: white; padding: 14px 32px; border-radius: 8px; font-weight: 600; border: none; cursor: pointer; font-size: 1rem; box-shadow: 0 4px 16px rgba(37,99,235,0.4); }}
  .features {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; padding: 60px 48px; max-width: 1200px; margin: 0 auto; }}
  .card {{ background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 32px; }}
  .card h3 {{ font-size: 1.3rem; margin-bottom: 10px; color: #38bdf8; }}
  .card p {{ color: #94a3b8; font-size: 0.95rem; }}
  footer {{ text-align: center; padding: 40px; color: #64748b; border-top: 1px solid rgba(255,255,255,0.06); font-size: 0.85rem; }}
</style>
</head>
<body>
<header>
  <div class="logo">⚡ {title}</div>
  <button class="btn" style="padding: 10px 24px; font-size: 0.85rem;" onclick="alert('Get Started clicked!')">Get Started</button>
</header>
<div class="hero">
  <h1>Next-Generation Platform for <span class="gradient">{title}</span></h1>
  <p class="lead">Accelerating modern workflows with intelligent automation, clean interfaces, and resilient infrastructure.</p>
  <button class="btn" onclick="alert('Trial started!')">Start Free Today</button>
</div>
<div class="features">
  <div class="card">
    <h3>Intelligent Engine</h3>
    <p>Automate complex repetitive processes with sub-second decision making and autonomous workflows.</p>
  </div>
  <div class="card">
    <h3>Enterprise Security</h3>
    <p>End-to-end encrypted protocol execution ensuring your mission-critical operations remain confidential.</p>
  </div>
  <div class="card">
    <h3>Instant Deployment</h3>
    <p>Zero-configuration launch in any modern browser or cloud runtime with automated scaling.</p>
  </div>
</div>
<footer>
  <p>© 2026 {title} • Generated with Iris AI</p>
</footer>
</body>
</html>"""
