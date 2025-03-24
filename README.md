# Teams background randomizer
Select a random background image for Microsoft Teams.
If you use the daily job, it will give you a new file every day to use as your background.

> Warning: This script will remove all other uploaded background files.

## Setup

Download this repository to any place on your machine and setup the python environment with:

```bash
pipenv install
```

Configure your settings by copying the `config.example.yaml` to `config.yaml` file and adjust the settings to your setup.

After that the script can be executed from the project dir with:

```bash
pipenv run randomizer
```

To execute the script from anywhere on your host, use the script which sets the project environment right:

```bash
# Switch to the
cd ~/Workspace/teams-background-randomizer
pipenv run randomizer

# Or as one-liner
cd ~/Workspace/teams-background-randomizer/scripts/runRandomizer.sh
```

## Run it on a regular interval

To let it run daily or every hour the preferred way is to use cron.
To edit the cron file on Linux / MacOS execute the following commands

> On MacOS make sure cron is allowed to have [file access on your host](https://apple.stackexchange.com/a/378558).

```shell
# This will open the crontab file to edit
crontab -e

# Add a line when your script should be executed. See the two sample lines
# Execute it every minute - Useful for debugging
*/1 * * * * ~/Workspace/teams-background-randomizer/scripts/runRandomizer.sh
# Execute it every hour
0 */1 * * * ~/Workspace/teams-background-randomizer/scripts/runRandomizer.sh
# Execute it on startup
@reboot ~/Workspace/teams-background-randomizer/scripts/runRandomizer.sh
```

## How it works

The algorithm goes like this:

1. Collect all background images from the image_source_dir
2. Read the history file, how often every image was shown already
3. Choose a new background randomly with weights. The less shown, the more likely it will be chosen.
4. Copy it to a cache folder
5. If enabled draw the logo with in dark or light variant on the background
6. If enabled save the modified image also in the cache folder
7. Replace or Set a hard link in the MS Teams upload folder. (If no hard link is found the first uploaded image will be replaced with it)
8. MS Teams will now pick up the link to the random image in the cache folder
