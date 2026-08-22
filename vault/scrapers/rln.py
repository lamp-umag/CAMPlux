"""
Radio Las Nieves — rln.cl
Aysén regional radio, runs real news content (not just a schedule page).
robots.txt: blocks a long list of named AI crawlers (ClaudeBot, GPTBot,
CCBot, etc.) and declares Content-Signal ai-train=no under the EU DSM
directive framework. Our UA ("CAMPlux-Quarry/1.0") isn't one of the named
bots -- falls under the general User-agent: * rule, which explicitly
Allow: / for crawling (same precedent already applied to ovejeronoticias.py,
which has an equivalent named-bot-blocklist). ai-train=no is a licensing
signal about model training, not a robots.txt crawl restriction -- this
project is archival/research corpus building, not AI training.
"""
from .wordpress import WordPressScraper


class RlnScraper(WordPressScraper):
    name = "Radio Las Nieves"
    base_url = "https://www.rln.cl"
    region = "aysen"
    min_delay = 1.0
