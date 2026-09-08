cd document \
&& npx md-to-pdf \
  --launch-options='{"args":["--no-sandbox"]}' \
  --basedir=. \
  --css='img { max-width: 100%; height: auto; }' \
  /home/ky2001/OneDrive/Linux/fx-trading-simulator-api/document/day2/one-pager.md
