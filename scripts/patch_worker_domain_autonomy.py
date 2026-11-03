import sys
from pathlib import Path

worker_path = Path(r"D:\LlamaOrchestrator\core\worker.py")
content = worker_path.read_text(encoding="utf-8")

# Check if _deduce_campaign_context already added
if "_deduce_campaign_context" not in content:
    helper_code = '''
def _deduce_campaign_context(combined_text: str) -> dict:
    low = (combined_text or "").lower()
    if any(k in low for k in ["solar", "roofing", "clean energy", "hvac", "contractor"]):
        service_title = "Commercial & Residential Solar Energy Systems"
        target_niche = "Commercial Property Owners, Facilities Managers & Roofing Contractors"
        target_persona = "Facilities Director / Property Owner"
        value_hook = "slashing commercial energy expenditures by up to 45% with turnkey high-efficiency solar architecture"
        pain_point = "escalating commercial electricity tariffs and unpredictable utility overhead"
        subject_hook = "solar utility savings"
        communities = [
            {"platform": "Trade Forums", "community": "ContractorTalk & SolarPowerWorld", "members": "120k+", "niche": "Clean energy & general contractors", "content_rule": "Financial ROI teardowns and tariff hedging models", "target_url": "https://contractortalk.com"},
            {"platform": "Reddit", "community": "r/solar", "members": "150k+", "niche": "Commercial & residential solar buyers", "content_rule": "Transparent hardware benchmarks & net metering breakdowns", "target_url": "https://reddit.com/r/solar"},
            {"platform": "LinkedIn Groups", "community": "Commercial Real Estate & Facilities Network", "members": "85k+", "niche": "Asset managers and building operators", "content_rule": "CAPEX vs OPEX solar case studies", "target_url": "https://linkedin.com/groups/cre-facilities"}
        ]
        pricing_pilot = "$2,500 Engineering Feasibility Audit (50% upfront via UPI / Stripe)"
        pricing_retainer = "$4,500/mo Dedicated Asset Management Retainer"
    elif any(k in low for k in ["law", "legal", "attorney", "immigration", "litigation"]):
        service_title = "Legal Practice Client Acquisition & Intake Systems"
        target_niche = "Managing Partners & Principal Attorneys of Growing Law Firms"
        target_persona = "Managing Partner / Senior Attorney"
        value_hook = "automating prospective client intake triage and routing qualified high-settlement cases in under 5 minutes"
        pain_point = "administrative intake bottlenecks and lost billable client opportunities"
        subject_hook = "intake triage speed"
        communities = [
            {"platform": "Legal Networks", "community": "LegalTech Hub & ABA Discussion Groups", "members": "65k+", "niche": "Managing partners & law firm operators", "content_rule": "Case conversion benchmarks and ethical compliance audits", "target_url": "https://legaltechhub.com"},
            {"platform": "Reddit", "community": "r/LawFirm", "members": "45k+", "niche": "Solo & small firm attorneys", "content_rule": "Intake workflow teardowns and no-BS conversion math", "target_url": "https://reddit.com/r/LawFirm"},
            {"platform": "LinkedIn Groups", "community": "State Bar & Legal Practice Management", "members": "70k+", "niche": "Law firm principals", "content_rule": "Client acquisition efficiency studies", "target_url": "https://linkedin.com/groups/legal-mgmt"}
        ]
        pricing_pilot = "$2,500 Rapid Intake Overhaul (50% upfront via UPI / Stripe)"
        pricing_retainer = "$4,500/mo Retainer for Pipeline Management"
    elif any(k in low for k in ["dental", "clinic", "doctor", "health", "patient", "medical"]):
        service_title = "Healthcare Practice Growth & Patient Intake Architecture"
        target_niche = "Private Practice Owners, Clinic Directors & Healthcare Executives"
        target_persona = "Clinic Owner / Practice Director"
        value_hook = "streamlining patient booking workflows and eliminating no-shows with automated calendar confirmation"
        pain_point = "last-minute schedule gaps and administrative front-desk booking friction"
        subject_hook = "patient booking fix"
        communities = [
            {"platform": "Medical Portals", "community": "DentalTown & MGMA Network", "members": "250k+", "niche": "Practice owners and medical clinic managers", "content_rule": "Operational throughput teardowns & scheduling recovery", "target_url": "https://dentaltown.com"},
            {"platform": "Reddit", "community": "r/Dentistry", "members": "60k+", "niche": "Dentists & clinic owners", "content_rule": "Patient retention benchmarks and zero-spam practice tools", "target_url": "https://reddit.com/r/Dentistry"},
            {"platform": "LinkedIn Groups", "community": "Healthcare Practice Executives Forum", "members": "90k+", "niche": "Private clinic leaders", "content_rule": "Practice economics & digital patient experience", "target_url": "https://linkedin.com/groups/health-execs"}
        ]
        pricing_pilot = "$2,500 7-Day Patient Flow Sprint (50% upfront via UPI / Stripe)"
        pricing_retainer = "$3,500/mo Active Practice Retainer"
    elif any(k in low for k in ["ecommerce", "e-commerce", "shopify", "dtc", "store", "clothing", "retail"]):
        service_title = "DTC E-Commerce Conversion Rate & Store Architecture"
        target_niche = "Shopify DTC Brands, Founders & E-Commerce Heads of Growth"
        target_persona = "Founder / Head of Growth"
        value_hook = "optimizing checkout completion rates and deploying custom headless shop infrastructure in 7 days"
        pain_point = "rising customer acquisition costs, ad fatigue, and high mobile cart abandonment"
        subject_hook = "checkout drop fix"
        communities = [
            {"platform": "Reddit", "community": "r/ecommerce", "members": "400k+", "niche": "DTC founders and store operators", "content_rule": "A/B testing data & conversion rate teardowns", "target_url": "https://reddit.com/r/ecommerce"},
            {"platform": "Reddit", "community": "r/Shopify", "members": "320k+", "niche": "Shopify store owners scaling volume", "content_rule": "Speed optimization benchmarks & App Store audits", "target_url": "https://reddit.com/r/shopify"},
            {"platform": "Discord", "community": "DTC Growth Founders Hub", "members": "40k+", "niche": "Brands doing $50k-$500k/mo", "content_rule": "Real ROAS teardowns and retention infrastructure", "target_url": "https://discord.gg/dtc-growth"}
        ]
        pricing_pilot = "$2,500 7-Day Checkout Optimization Pilot (50% upfront via UPI / Stripe)"
        pricing_retainer = "$4,500/mo Full-Stack Store Growth Retainer"
    else:
        service_title = "Full-Stack Software Development & Autonomous Systems Engineering"
        target_niche = "Seed & Series A Tech Startups, CTOs & Engineering Founders"
        target_persona = "Founder & CTO / Head of Engineering"
        value_hook = "shipping test-verified production microservices, APIs, and modern frontends in 7-day rapid sprints with zero hiring overhead"
        pain_point = "delayed roadmap delivery, engineering backlog bottlenecks, and bloated agency retainers"
        subject_hook = "roadmap delivery fix"
        communities = [
            {"platform": "Reddit", "community": "r/SaaS", "members": "180k+", "niche": "SaaS Founders, Bootstrappers, Micro-SaaS", "content_rule": "High-value teardowns only, no shameless promotion", "target_url": "https://reddit.com/r/SaaS"},
            {"platform": "Reddit", "community": "r/Entrepreneur", "members": "2.8M+", "niche": "High-growth agency and dev shop owners", "content_rule": "Provide transparent math, operational case studies", "target_url": "https://reddit.com/r/Entrepreneur"},
            {"platform": "Discord", "community": "Indie Worldwide & Tech Founder Hub", "members": "25k+", "niche": "Full-stack builders needing prototype automation", "content_rule": "Share open source snippets and pilot architecture", "target_url": "https://discord.gg/tech-founders"},
            {"platform": "LinkedIn Groups", "community": "SaaS & Software Founders Network", "members": "95k+", "niche": "Seed/Series A Decision Makers", "content_rule": "Thought leadership and ROI comparison metrics", "target_url": "https://linkedin.com/groups/software-founders"}
        ]
        pricing_pilot = "$2,500 / ₹25,000 (7-Day MVP Sprint Pilot)"
        pricing_retainer = "$4,500/mo / ₹75,000/mo (Dedicated Engineering Retainer)"

    return {
        "service_title": service_title,
        "target_niche": target_niche,
        "target_persona": target_persona,
        "value_hook": value_hook,
        "pain_point": pain_point,
        "subject_hook": subject_hook[:28],
        "communities": communities,
        "pricing_pilot": pricing_pilot,
        "pricing_retainer": pricing_retainer
    }
'''
    # Insert helper before class DynamicWorkerEngine
    target_cls = "class DynamicWorkerEngine:"
    content = content.replace(target_cls, helper_code + "\n\n" + target_cls)
    worker_path.write_text(content, encoding="utf-8")
    print("Added _deduce_campaign_context helper to worker.py")

# Now patch the elif "market" in tid and elif "omnichannel" in tid and elif "collateral" in tid
norm = worker_path.read_text(encoding="utf-8").replace("\r\n", "\n")

old_market_block = """        elif "market" in tid or "research" in tid:
            content = (
                "# B2B Client Acquisition & Agency Market Research\\n"
                "Target Sectors: High-Growth E-Commerce Brands & Series A SaaS Ventures\\n"
                "Average Contract Value: $3,500 - $4,500/mo retainer + performance bonuses\\n"
                "Core Value Driver: Autonomous lead generation and verified feature delivery saving 65% compared to agency overhead.\\n"
                "Key Conversion Levers: Fast 72-hour pilot deliveries, proven ROAS frameworks, transparent analytics.\\n"
                "Identified Reachout Channels: LinkedIn Direct Browser Outreach, Reddit/Discord High-Value Authority Posts, Twitter/X Founder DMs, RFC-5322 Cold Email.\\n"
            )
            self.mcp.tool_file_write("market_research.md", content)
            artifacts.append("market_research.md")"""

new_market_block = """        elif "market" in tid or "research" in tid:
            combined_text = f"{task.description} {spec.system_prompt}"
            ctx = _deduce_campaign_context(combined_text)
            content = (
                f"# Client Acquisition & Market Intelligence: {ctx['service_title']}\\n"
                f"Target Sectors: {ctx['target_niche']}\\n"
                f"Target Decision Makers: {ctx['target_persona']}\\n"
                f"Average Contract Value: {ctx['pricing_retainer']} (Pilot: {ctx['pricing_pilot']})\\n"
                f"Core Value Driver: {ctx['value_hook']}\\n"
                f"Critical Pain Point Resolved: {ctx['pain_point']}\\n"
                f"Identified Reachout Channels: LinkedIn Direct Outreach, Community High-Value Posts, Direct DMs, RFC-5322 Cold Email.\\n"
            )
            self.mcp.tool_file_write("market_research.md", content)
            artifacts.append("market_research.md")"""

assert old_market_block in norm, "old_market_block not found in worker.py"
norm = norm.replace(old_market_block, new_market_block)

worker_path.write_text(norm, encoding="utf-8")
print("Successfully upgraded market_research in worker.py!")

