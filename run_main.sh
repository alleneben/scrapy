
#!/bin/sh

. ~/igroup/venv/bin/activate

cd ~/igroup/igroup/coupons

nohup python main.py > main_nohup.out 2> main_nohup.err < /dev/null &
