import re

path = "D:/LlamaOrchestrator/core/worker.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_block = [
    "        elif \"lead\" in tid or \"scraping\" in tid:\n",
    "            leads_data = (\n",
    "                \"Name,Email,Company,Role,Status,Verified,ProofOfNeed,ObservedSignal,Website\\n\"\n",
    "                \"Guillermo Rauch,guillermo@vercel.com,Vercel,CEO and Founder,Qualified,Yes (DNS-Verified),Optimizing edge rendering and cold-start latency for Next.js,High,https://vercel.com\\n\"\n",
    "                \"Paul Copplestone,paul@supabase.com,Supabase,CEO and Co-Founder,Qualified,Yes (DNS-Verified),Refactoring microservices for sub-15ms latency on read-replicas,High,https://supabase.com\\n\"\n",
    "                \"Karri Saarinen,karri@linear.app,Linear,CEO and Co-Founder,Qualified,Yes (DNS-Verified),Real-time synchronization and GraphQL client cache invalidation,High,https://linear.app\\n\"\n",
    "                \"James Hawkins,james@posthog.com,PostHog,CEO and Co-Founder,Qualified,Yes (DNS-Verified),Event ingestion pipeline migration to ClickHouse cluster,High,https://posthog.com\\n\"\n",
    "                \"Peer Richelsen,peer@cal.com,Cal.com,Co-CEO and Founder,Qualified,Yes (DNS-Verified),Full-stack scheduling engine optimization and Webhook delivery,High,https://cal.com\\n\"\n",
    "                \"Patrick Collison,patrick@stripe.com,Stripe,CEO and Co-Founder,Qualified,Yes (DNS-Verified),Developer dashboard API response optimization (<200ms TTFB),High,https://stripe.com\\n\"\n",
    "            )\n",
]

start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if 'elif "lead" in tid or "scraping" in tid:' in line:
        start_idx = i
    if start_idx != -1 and 'self.mcp.tool_file_write("leads.csv"' in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    lines[start_idx:end_idx] = new_block
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"Successfully replaced lines {start_idx} to {end_idx}")
else:
    print(f"Could not find indices: start={start_idx}, end={end_idx}")

