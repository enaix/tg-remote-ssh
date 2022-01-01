#!/bin/bash

if (( $UID == 0 )); then
	echo "Please run as non-priviledged user"
	exit
fi

CUR_USER="$(id -u -n)"

FILES="$(find -name '*.service')"
WORKING_DIR="$(pwd)"

echo "Parsing .service files..."

for f in $FILES; do
	sed -i "s/cur_user/$CUR_USER/g" $f
	sed -i "s/cur_group/$CUR_USER/g" $f
	sed -i "s/working_dir/$WORKING_DIR/g" $f
done

echo "Copying services to /etc/systemd/system/multi-user.target.wants ..."

for f in $FILES; do
	sudo cp $f /etc/systemd/system/multi-user.target.wants/$f
done

echo "Done! Now you may enable/disable these services. View README.md for details"
