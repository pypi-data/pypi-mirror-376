from datetime import datetime

# COLORS
G = "\033[92m"  # GREEN
B = "\033[94m"  # BLUE
R = "\033[91m"  # RED
W = "\033[97m"  # WHITE
X = "\033[60m"  # GRAY
_ = "\033[0m"  # RESET

# EXPERIENCE
NOW = datetime.now()
YEARS = NOW.year - 2016
MONTHS = NOW.month - 6

EXP = f"{YEARS} years"

if MONTHS > 0:
    EXP += f" and {MONTHS} months"


# MESSAGE
MESSAGE = f"""
{G}Hello world!{_} 👋🏻️ 🌎

My name is {W}Fede Calendino{_}, I'm an Argentinian 🇦🇷 living in the UK 🇬🇧.

Creative and adaptable Software Engineer focused on back-end development with Python and Rust. 
Pragmatic problem-solver with a strong analytical mindset. 
Experienced in building scalable APIs, automating infrastructure, and improving performance. 
Thrives in fast-paced teams, adapts quickly to new tools and domains, and values clean, maintainable, and testable code.


{R}Experience ({EXP}){_}:
* {W}Contractor Software Engineer at Book.io{_}{X} (Aug 2023 - Present){_}

* {W}Software Engineer II at Microsoft{_}{X} (May 2022 - Aug 2025){_}
* {W}Software Engineer at Glinvergy Inc.{_}{X} (Oct 2020 - Apr 2022){_}
* {W}Software Engineer at Reciprocity Labs{_}{X} (Oct 2019 - Sep 2020){_}
* {W}Software Engineer at uBiome{_}{X} (Mar 2018 - Jul 2019){_}
* {W}Java Developer at Globant{_}{X} (Jun 2016 - Feb 2018){_}


{R}Contact Information{_}:
✉️ {X}mailto:{W}federico@calendino.com{_}
💻 {X}https://{W}github.com/fedecalendino{_}
👤 {X}https://{W}linkedin.com/in/fedecalendino{_}
"""

if __name__ == "__main__":
    print(MESSAGE)
