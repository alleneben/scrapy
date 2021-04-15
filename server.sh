
#!/bin/sh

. ~/igroup/venv/bin/activate

cd ~/igroup/igroup/coupons

nohup scrapyd > nohup.out 2> nohup.err < /dev/null &
