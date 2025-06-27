cd /git/Autoresuscitation
git fetch || echo ERROR && exit /b
git checkout com_int_wip || echo ERROR && exit /b
git reset --hard com_int_wip || echo ERROR && exit /b
uv run fm_reporting_email.py || echo ERROR && exit /b