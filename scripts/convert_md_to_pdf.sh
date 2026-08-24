cd document \
&& npx md-to-pdf \
  --launch-options='{"args":["--no-sandbox"]}' \
  --basedir=. \
  --css='img { max-width: 100%; height: auto; }' \
  how_to_use_colab.md
