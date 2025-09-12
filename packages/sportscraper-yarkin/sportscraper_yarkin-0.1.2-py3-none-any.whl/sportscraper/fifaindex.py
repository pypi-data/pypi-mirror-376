from __future__ import annotations
import logging
import time
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd
from tqdm import tqdm
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .utils import retry, initialize_driver


def _accept_shadow_cookie(driver) -> None:
    """
    Attempts to accept the cookie consent that FIFAIndex serves via a shadow DOM.
    No-op if not present.
    """
    try:
        shadow_host = driver.find_element(By.CSS_SELECTOR, "#cmpwrapper")
        shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)
        accept_button = shadow_root.find_element(By.CSS_SELECTOR, "#cmpwelcomebtnyes")
        accept_button.click()
        time.sleep(1)
    except Exception as e:  # cookie prompt can be absent or different per geo/version
        logging.debug("Cookie popup not handled (likely absent): %s", e)


@retry(max_attempts=3, delay=5, logger=logging.getLogger(__name__))
def get_team_links_df(teams_url: str, version_label: str, headless: bool = True) -> pd.DataFrame:
    """
    Scrape team names and URLs for a given FIFAIndex teams listing URL.
    """
    driver = initialize_driver(headless=headless)
    try:
        driver.get(teams_url)
        _accept_shadow_cookie(driver)

        team_links = driver.find_elements(By.CSS_SELECTOR, "table.table-teams a.link-team")
        team_data = {(el.text.strip(), el.get_attribute("href"))
                     for el in team_links if el.text.strip() and el.get_attribute("href")}

        df = pd.DataFrame(sorted(team_data), columns=["Team Name", "Team URL"])
        df["Version"] = version_label
        logging.info("Extracted %d teams from %s (%s)", len(df), teams_url, version_label)
        return df
    finally:
        driver.quit()


@retry(max_attempts=3, delay=5, logger=logging.getLogger(__name__))
def get_player_links(team_url: str, team_name: str, headless: bool = True) -> pd.DataFrame:
    """
    Scrape player names and URLs from a team page.
    """
    driver = initialize_driver(headless=headless)
    try:
        driver.get(team_url)
        _accept_shadow_cookie(driver)

        elements = driver.find_elements(By.CSS_SELECTOR, "table.table-players a.link-player")
        player_data = {(el.text.strip(), el.get_attribute("href"))
                       for el in elements if el.text.strip() and el.get_attribute("href")}

        df = pd.DataFrame(sorted(player_data), columns=["Player Name", "Player URL"])
        df["Team Name"] = team_name
        df["Version"] = team_url.rstrip('/').split('/')[-1]
        logging.info("Extracted %d players from %s (%s)", len(df), team_name, df["Version"].iloc[0])
        return df
    finally:
        driver.quit()


@retry(max_attempts=3, delay=5, logger=logging.getLogger(__name__))
def scrape_sofifa_player_stats(player_url: str, team_name: str, version: str, headless: bool = True) -> pd.DataFrame:
    """
    Scrape one player's stat cards into a single-row DataFrame with stat names as columns.
    """
    driver = initialize_driver(headless=headless)
    try:
        driver.get(player_url)
        _accept_shadow_cookie(driver)

        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "card")))

        desired_categories = {
            "Ball Skills", "Passing", "Shooting", "Defence", "Physical", "Mental", "Goalkeeper"
        }

        player_stats: Dict[str, str] = {}
        for card in driver.find_elements(By.CLASS_NAME, "card"):
            try:
                category = card.find_element(By.CLASS_NAME, "card-header").text.strip()
                if category not in desired_categories:
                    continue
                body = card.find_element(By.CLASS_NAME, "card-body")
                for p in body.find_elements(By.TAG_NAME, "p"):
                    # left side label is the stat name, right side is value
                    stat_name = p.text.split('\n')[0].strip()
                    stat_value = p.find_element(By.CLASS_NAME, "float-right").text.strip()
                    player_stats[stat_name] = stat_value
            except Exception as e:
                logging.debug("Skipping a stat card due to error: %s", e)
                continue

        df = pd.DataFrame([player_stats])
        df.insert(0, "Player Name", None)
        df.at[0, "Player Name"] = driver.title.split(" | ")[0] if " | " in driver.title else ""
        df["Team"] = team_name
        df["Version"] = version
        return df
    finally:
        driver.quit()


@retry(max_attempts=3, delay=5, logger=logging.getLogger(__name__))
def get_player_stats_from_team(team_players_df: pd.DataFrame, headless: bool = True) -> pd.DataFrame:
    """
    Given a DataFrame of players (columns: Player Name, Player URL, Team Name, Version),
    fetch all player stats and return a concatenated DataFrame.
    """
    rows: List[pd.DataFrame] = []
    for _, row in team_players_df.iterrows():
        purl = row["Player URL"]
        pname = row["Player Name"]
        tname = row["Team Name"]
        version = row["Version"]
        logging.info("Scraping stats: %s (%s, %s)", pname, tname, version)
        try:
            stats_df = scrape_sofifa_player_stats(purl, tname, version, headless=headless)
            stats_df["Player Name"] = pname  # ensure consistent value
            rows.append(stats_df)
        except Exception as e:
            logging.error("Failed scraping %s: %s", pname, e)
            continue
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_year_url_map(
    start_year_infix: int = 16,
    end_year_infix: int = 24,
    league_id: int = 13
) -> Dict[int, str]:
    """
    Build a dict {19: 'https://www.fifaindex.com/teams/fifa19/?league=13&order=desc', ...}
    using FIFA 'infix' years (e.g., 16 -> fifa16).
    """
    return {
        i: f"https://www.fifaindex.com/teams/fifa{i}/?league={league_id}&order=desc"
        for i in range(start_year_infix, end_year_infix + 1)
    }


def run_full_scrape(
    start_year_infix: int = 16,
    end_year_infix: int = 24,
    league_id: int = 13,
    outdir: str | Path = ".",
    headless: bool = True
) -> Tuple[Path, Path, Path]:
    """
    High-level driver:
      1) collect teams for each year,
      2) collect players for each team,
      3) scrape player stats per team (checkpointing),
      4) return paths to CSV outputs.
    """
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)

    # Logging to file in outdir
    logging.basicConfig(
        filename=str(out / "fifaindex_scraper.log"),
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filemode="a"
    )
    logging.info("==== FIFAIndex scrape started ====")

    year_urls = build_year_url_map(start_year_infix, end_year_infix, league_id)
    fifa_years_list = list(year_urls.keys())

    # Step 1: Teams
    all_teams_df = pd.DataFrame()
    for y in tqdm(fifa_years_list, desc="Collecting teams"):
        try:
            tmp = get_team_links_df(year_urls[y], f"fifa{y}", headless=headless)
            all_teams_df = pd.concat([all_teams_df, tmp], ignore_index=True)
            time.sleep(1.5)
        except Exception as e:
            logging.error("Error gathering teams for FIFA %s: %s", y, e)
            continue
    teams_csv = out / "teams.csv"
    all_teams_df.to_csv(teams_csv, index=False)

    # Step 2: Players
    all_players_df = pd.DataFrame()
    for _, row in tqdm(all_teams_df.iterrows(), total=len(all_teams_df), desc="Collecting players"):
        try:
            players_df = get_player_links(row["Team URL"], row["Team Name"], headless=headless)
            all_players_df = pd.concat([all_players_df, players_df], ignore_index=True)
        except Exception as e:
            logging.error("Error gathering players for %s: %s", row["Team Name"], e)
    players_csv = out / "players.csv"
    all_players_df.to_csv(players_csv, index=False)

    # Step 3: Player stats (team batching + checkpointing)
    checkpoint = out / "player_stats_checkpoint.csv"
    final_csv = out / "player_stats_final.csv"
    if checkpoint.exists():
        all_stats_df = pd.read_csv(checkpoint)
        scraped = set(zip(all_stats_df.get("Team", []), all_stats_df.get("Version", [])))
    else:
        all_stats_df = pd.DataFrame()
        scraped = set()

    grouped = all_players_df.groupby(["Team Name", "Version"])
    for (team_name, version), group in tqdm(grouped, desc="Scraping team stats"):
        if (team_name, version) in scraped:
            continue
        try:
            stats_df = get_player_stats_from_team(group, headless=headless)
            all_stats_df = pd.concat([all_stats_df, stats_df], ignore_index=True)
            all_stats_df.to_csv(checkpoint, index=False)
            logging.info("Scraped stats for %s (%s)", team_name, version)
        except Exception as e:
            logging.error("Failed scraping %s (%s): %s", team_name, version, e)
            continue

    all_stats_df.to_csv(final_csv, index=False)
    logging.info("==== FIFAIndex scrape completed ====")
    return teams_csv, players_csv, final_csv
