#!/bin/bash

libraries=("ttkbootstrap" "ttkthemes" "chlorophyll" "PIL" "pillow")

get_library_path() {
    library=$1
    library_path=$(pip show "$library" | grep "Location:" | awk '{print $2}')
    echo "$library_path"
}

script_root=$(dirname "$(realpath "$0")")
icon_path="$script_root/software.ico"
img_path="$script_root/software.png"
script_path="$script_root/Organizer_linux.py"

pyinstaller_cmd="pyinstaller --noconfirm --onefile --windowed --distpath Organizer --icon \"$icon_path\" --add-data \"$img_path:.\" --add-data \"$icon_path:.\" --add-data \"$script_root/_internal:_internal/\" --add-data \"$script_root/plugins:plugins/\""

for library in "${libraries[@]}"; do
    library_path=$(get_library_path "$library")

    if [ -n "$library_path" ]; then
        echo "Library Path for '$library' is: $library_path"
        
        pyinstaller_cmd+=" --add-data \"$library_path/$library:$library/\""
    else
        echo "Library Path not found for '$library'"
    fi
done

pyinstaller_cmd+=" \"$script_path\""

echo "Building .exe file for Organizer..."
eval "$pyinstaller_cmd"
echo "Organizer.exe Build complete"
