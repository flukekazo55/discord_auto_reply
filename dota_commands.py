import httpx
from bs4 import BeautifulSoup

async def get_dota_meta_by_position():
    url = "https://dotacoach.gg/en/heroes/meta"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
    if resp.status_code != 200:
        return f"Website error (status {resp.status_code})"
    soup = BeautifulSoup(resp.text, "html.parser")

    sections = soup.select(".role-meta")
    if not sections:
        return "NOT FOUND META"

    output = ["Meta pick rates by position:"]
    for sec in sections:
        role = sec.find("h3").get_text(strip=True)
        rows = sec.select("tbody tr")[:3]
        heroes = []
        for r in rows:
            cols = r.find_all("td")
            name = cols[1].get_text(strip=True)
            pick = cols[2].get_text(strip=True)
            heroes.append(f"{name} ({pick})")
        output.append(f"{role}: {', '.join(heroes)}")
    return "\n".join(output)

async def get_dota_counters(hero_name: str):
    hero = hero_name.lower().replace(" ", "-")
    url = f"https://dotacoach.gg/en/heroes/counters/{hero}"
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
        
    if resp.status_code != 200:
        return f"No hero counter for '{hero_name}'"

    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.select("tbody tr")[:3]
    if not rows:
        return f"No hero counter for '{hero_name}'"

    counters = []
    for r in rows:
        cols = r.find_all("td")
        name = cols[1].get_text(strip=True)
        adv = cols[2].get_text(strip=True)
        counters.append(f"{name} (Advantage: {adv})")
    return f"Counters hero for {hero_name.title()}:\n" + "\n".join(counters)

async def handle_dota_command(message):
    content = message.content.lower().strip()
    
    if content.startswith("/fdm"):
        await message.channel.typing()
        msg = await get_dota_meta_by_position()
        await message.reply(msg)
        return True
        
    if content.startswith("/fdc"):
        parts = content.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply("Please typing: `/fdc Phantom Assassin`")
            return True
        hero = parts[1]
        await message.channel.typing()
        msg = await get_dota_counters(hero)
        await message.reply(msg)
        return True
    
    return False
