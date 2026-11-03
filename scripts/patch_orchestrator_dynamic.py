import sys
from pathlib import Path

orch_path = Path(r"D:\LlamaOrchestrator\core\orchestrator.py")
content = orch_path.read_text(encoding="utf-8")

norm = content.replace("\r\n", "\n")

old_block = '''            clarifications = [
                ClarificationQuestion(
                    id="target_niche",
                    question="Which industry niche should we target for immediate high-ticket client acquisition?",
                    why_needed="Focuses cold outreach copy on exact technical pain points and engineering bottlenecks.",
                    options=["Seed & Series A AI/SaaS Startups", "High-Growth DTC & E-Commerce Meta Ads Brands", "Healthcare & MedTech Platforms", "Local Businesses Needing AI Automation"],
                    default_selection="Seed & Series A AI/SaaS Startups"
                ),
                ClarificationQuestion(
                    id="pricing_model",
                    question="What pricing and offer structure should we scaffold for your first 5 clients?",
                    why_needed="Ensures immediate cashflow while de-risking the engagement for prospective founders.",
                    options=["$2,500 Pilot Sprint + $4,500/mo Retainer", "₹25,000 Pilot + ₹50,000/mo Retainer", "Pure Equity & Rev-Share", "Hourly Billing ($150/hr)"],
                    default_selection="$2,500 Pilot Sprint + $4,500/mo Retainer"
                ),
                ClarificationQuestion(
                    id="closing_strategy",
                    question="How should Jarvis decide to close prospective clients for you?",
                    why_needed="Determines whether Jarvis provides a 15-min discovery call link for Master Ansh or attempts to close pilots over direct messaging.",
                    options=[
                        "Hybrid: Close low-friction pilots over direct message/email; schedule 15-min discovery call with Master Ansh for retainers",
                        "Always schedule 15-min video call with Master Ansh (Calendly / Google Meet)",
                        "Direct close over email/message with instant payment link & UPI QR"
                    ],
                    default_selection="Hybrid: Close low-friction pilots over direct message/email; schedule 15-min discovery call with Master Ansh for retainers"
                ),
                ClarificationQuestion(
                    id="payment_details",
                    question="What payment settlement method should Jarvis embed in proposals & invoices to collect funds directly for you?",
                    why_needed="Ensures client retainers and pilot deposits flow directly into Master Ansh's account.",
                    options=[
                        "Master's UPI ID (anshtiwarisocial@gmail.com / UPI ID) & 50% upfront deposit",
                        "Stripe / Razorpay Invoice Payment Link",
                        "Direct Bank Wire / Invoice Net-15"
                    ],
                    default_selection="Master's UPI ID (anshtiwarisocial@gmail.com / UPI ID) & 50% upfront deposit"
                ),
                ClarificationQuestion(
                    id="scheduling_link",
                    question="Which scheduling link should Jarvis provide to clients for booking discovery calls with Master Ansh?",
                    why_needed="Enables prospective clients to directly book slots on Master Ansh's calendar.",
                    options=[
                        "Master's Calendly / Cal.com link (e.g. calendly.com/anshtiwari)",
                        "Google Meet invite generated via Master's Google Workspace",
                        "Direct WhatsApp scheduling confirmation"
                    ],
                    default_selection="Master's Calendly / Cal.com link (e.g. calendly.com/anshtiwari)"
                ),
                ClarificationQuestion(
                    id="outbound_angle",
                    question="Which cold outreach messaging angle converts highest for your skill profile?",
                    why_needed="Shapes the 3-sentence email templates to maximize founder reply rate.",
                    options=["Rapid 7-Day Sprint Delivery (Zero Hiring Overhead)", "Multi-Agent Automation Audit", "Code Quality & Telemetry Modernization"],
                    default_selection="Rapid 7-Day Sprint Delivery (Zero Hiring Overhead)"
                )
            ]
            recommended_defaults = {
                "target_niche": "Seed & Series A AI/SaaS Startups",
                "pricing_model": "$2,500 Pilot Sprint + $4,500/mo Retainer",
                "closing_strategy": "Hybrid: Close low-friction pilots over direct message/email; schedule 15-min discovery call with Master Ansh for retainers",
                "payment_details": "Master's UPI ID (anshtiwarisocial@gmail.com / UPI ID) & 50% upfront deposit",
                "scheduling_link": "Master's Calendly / Cal.com link (e.g. calendly.com/anshtiwari)",
                "outbound_angle": "Rapid 7-Day Sprint Delivery (Zero Hiring Overhead)"
            }'''

new_block = '''            # Dynamic Domain Niche Deduction from vision
            deduced_niche = "Seed & Series A AI/SaaS Startups"
            if any(w in v_lower for w in ["full stack", "fullstack", "dev", "developer", "software", "engineering"]):
                deduced_niche = "Full-Stack Development & Custom Systems Engineering"
            elif any(w in v_lower for w in ["solar", "roof", "roofing", "energy", "clean"]):
                deduced_niche = "Commercial & Residential Solar Energy Systems"
            elif any(w in v_lower for w in ["law", "legal", "attorney", "lawyer", "bar"]):
                deduced_niche = "Legal Practice Client Acquisition & Intake"
            elif any(w in v_lower for w in ["dental", "clinic", "health", "doctor", "medical"]):
                deduced_niche = "Healthcare & Private Dental Practices"
            elif any(w in v_lower for w in ["ecom", "ecommerce", "shopify", "dtc", "store"]):
                deduced_niche = "High-Growth DTC & E-Commerce Brands"

            deduced_pricing = "$2,500 Pilot Sprint + $4,500/mo Retainer"
            if "retainer" in v_lower and ("pilot" not in v_lower and "sprint" not in v_lower):
                deduced_pricing = "Monthly Retainer ($4,500/mo / ₹75,000/mo)"
            elif "equity" in v_lower:
                deduced_pricing = "Pure Equity & Rev-Share"

            clarifications = [
                ClarificationQuestion(
                    id="target_niche",
                    question="Which industry niche should we target for immediate high-ticket client acquisition?",
                    why_needed="Focuses cold outreach copy on exact technical pain points and engineering bottlenecks.",
                    options=[deduced_niche, "Seed & Series A AI/SaaS Startups", "High-Growth DTC & E-Commerce Brands", "Healthcare & MedTech Platforms", "Local Businesses Needing AI Automation"],
                    default_selection=deduced_niche
                ),
                ClarificationQuestion(
                    id="pricing_model",
                    question="What pricing and offer structure should we scaffold for your first 5 clients?",
                    why_needed="Ensures immediate cashflow while de-risking the engagement for prospective founders.",
                    options=[deduced_pricing, "$2,500 Pilot Sprint + $4,500/mo Retainer", "₹25,000 Pilot + ₹50,000/mo Retainer", "Hourly Billing ($150/hr)"],
                    default_selection=deduced_pricing
                ),
                ClarificationQuestion(
                    id="closing_strategy",
                    question="How should Jarvis decide to close prospective clients for you?",
                    why_needed="Determines whether Jarvis provides a 15-min discovery call link for Master Ansh or attempts to close pilots over direct messaging.",
                    options=[
                        "Hybrid: Close low-friction pilots over direct message/email; schedule 15-min discovery call with Master Ansh for retainers",
                        "Always schedule 15-min video call with Master Ansh (Calendly / Google Meet)",
                        "Direct close over email/message with instant payment link & UPI QR"
                    ],
                    default_selection="Hybrid: Close low-friction pilots over direct message/email; schedule 15-min discovery call with Master Ansh for retainers"
                ),
                ClarificationQuestion(
                    id="payment_details",
                    question="What payment settlement method should Jarvis embed in proposals & invoices to collect funds directly for you?",
                    why_needed="Ensures client retainers and pilot deposits flow directly into Master Ansh's account.",
                    options=[
                        "Master's UPI ID (anshtiwarisocial@gmail.com / UPI ID) & 50% upfront deposit",
                        "Stripe / Razorpay Invoice Payment Link",
                        "Direct Bank Wire / Invoice Net-15"
                    ],
                    default_selection="Master's UPI ID (anshtiwarisocial@gmail.com / UPI ID) & 50% upfront deposit"
                ),
                ClarificationQuestion(
                    id="scheduling_link",
                    question="Which scheduling link should Jarvis provide to clients for booking discovery calls with Master Ansh?",
                    why_needed="Enables prospective clients to directly book slots on Master Ansh's calendar.",
                    options=[
                        "Master's Calendly / Cal.com link (e.g. calendly.com/anshtiwari)",
                        "Google Meet invite generated via Master's Google Workspace",
                        "Direct WhatsApp scheduling confirmation"
                    ],
                    default_selection="Master's Calendly / Cal.com link (e.g. calendly.com/anshtiwari)"
                ),
                ClarificationQuestion(
                    id="outbound_angle",
                    question="Which cold outreach messaging angle converts highest for your skill profile?",
                    why_needed="Shapes the 3-sentence email templates to maximize founder reply rate.",
                    options=["Rapid 7-Day Sprint Delivery (Zero Hiring Overhead)", "Multi-Agent Automation Audit", "Code Quality & Telemetry Modernization"],
                    default_selection="Rapid 7-Day Sprint Delivery (Zero Hiring Overhead)"
                )
            ]
            recommended_defaults = {
                "target_niche": deduced_niche,
                "pricing_model": deduced_pricing,
                "closing_strategy": "Hybrid: Close low-friction pilots over direct message/email; schedule 15-min discovery call with Master Ansh for retainers",
                "payment_details": "Master's UPI ID (anshtiwarisocial@gmail.com / UPI ID) & 50% upfront deposit",
                "scheduling_link": "Master's Calendly / Cal.com link (e.g. calendly.com/anshtiwari)",
                "outbound_angle": "Rapid 7-Day Sprint Delivery (Zero Hiring Overhead)"
            }'''

assert old_block in norm, "old_block not found in orchestrator.py"
norm = norm.replace(old_block, new_block)

orch_path.write_text(norm, encoding="utf-8")
print("SUCCESS: core/orchestrator.py upgraded with dynamic domain deduction!")

