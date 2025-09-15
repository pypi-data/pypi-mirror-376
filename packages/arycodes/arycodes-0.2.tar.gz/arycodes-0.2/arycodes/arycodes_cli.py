import requests
import os
import textwrap
from tabulate import tabulate
from colorama import init, Fore, Style
from tkinter import Tk, filedialog

init(autoreset=True)
USERNAME = "arycodes"

# Helper function to wrap long text
def wrap_text(text, width=80):
    return "\n".join(textwrap.wrap(text, width))

# ---- List GitHub projects ----
def list_projects():
    url = f"https://api.github.com/users/{USERNAME}/repos"
    try:
        res = requests.get(url)
        res.raise_for_status()
        repos = res.json()
        if not repos:
            print(Fore.RED + "No repositories found.")
            return

        table = []
        for i, repo in enumerate(repos, start=1):
            table.append([
                i,
                repo['name'],
                wrap_text(repo['description'] or "No description", width=50),
                repo['language'] or "N/A",
                repo['stargazers_count']
            ])
        headers = [Fore.CYAN + "SNO.", "Repository Name", "Description", "Language", "Stars"]
        print("\n" + Fore.GREEN + "AryCodes GitHub Projects:")
        print(tabulate(table, headers=headers, tablefmt="fancy_grid"))
    except requests.RequestException:
        print(Fore.RED + "Failed to fetch projects from GitHub.")

# ---- View project details ----
def view_project():
    repo_name = input(Fore.YELLOW + "Enter repository name: ").strip()
    url = f"https://api.github.com/repos/{USERNAME}/{repo_name}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        repo = res.json()

        table = [
            ["Name", repo['name']],
            ["Description", wrap_text(repo['description'] or "No description", width=80)],
            ["Language", repo['language'] or "N/A"],
            ["Stars", repo['stargazers_count']],
            ["Forks", repo['forks_count']],
            ["URL", repo['html_url']]
        ]
        print("\n" + Fore.GREEN + "Project Details:")
        print(tabulate(table, tablefmt="fancy_grid"))
    except requests.RequestException:
        print(Fore.RED + "Repository not found or error fetching details.")

# ---- Download project with Save As popup ----
def download_project():
    repo_name = input(Fore.YELLOW + "Enter repository name to download: ").strip()
    zip_url = f"https://github.com/{USERNAME}/{repo_name}/archive/refs/heads/main.zip"
    try:
        res = requests.get(zip_url)
        res.raise_for_status()

        # Use Tkinter Save As dialog
        root = Tk()
        root.withdraw()  # Hide main window
        save_path = filedialog.asksaveasfilename(
            title="Save Project ZIP As",
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip")],
            initialfile=f"{repo_name}.zip"
        )
        if save_path:
            with open(save_path, "wb") as f:
                f.write(res.content)
            print(Fore.GREEN + f"Downloaded '{repo_name}' as '{save_path}'")
        else:
            print(Fore.YELLOW + "Download cancelled by user.")

    except requests.RequestException:
        print(Fore.RED + "Failed to download. Check if repository exists and main branch is correct.")

# ---- Interactive menu ----
def main():
    while True:
        print(Fore.CYAN + "\n=== AryCodes CLI ===")
        print(Fore.YELLOW + "1." + Fore.WHITE + " List GitHub Projects")
        print(Fore.YELLOW + "2." + Fore.WHITE + " View Project Details")
        print(Fore.YELLOW + "3." + Fore.WHITE + " Download Project (with Save As)")
        print(Fore.YELLOW + "4." + Fore.WHITE + " Exit")

        choice = input(Fore.GREEN + "Choose an option (1-4): ").strip()
        if choice == "1":
            list_projects()
        elif choice == "2":
            view_project()
        elif choice == "3":
            download_project()
        elif choice == "4":
            print(Fore.CYAN + "Exiting AryCodes CLI.")
            break
        else:
            print(Fore.RED + "Invalid option. Please enter 1-4.")

# Entry point for setup.py console script
if __name__ == "__main__":
    main()
